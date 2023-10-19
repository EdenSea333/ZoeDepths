import gradio as gr
import numpy as np
import trimesh
from geometry import depth_to_points, create_triangles
from functools import partial
import tempfile
import requests

id = 0 
free = 0
premium = 0

def set_user_information(_id, _free, _premium):
    global id, free, premium
    url = f"https://aianimationstg.wpengine.com/wp-json/customapi/v1/user-credit/{id}"
    headers = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36'}
    id = _id
    free = int(_free)
    premium = int(_premium)
    data = {
        'free':free,
        'premium':premium
    }
    requests.put(url, headers=headers, data=data)
def depth_edges_mask(depth):
    """Returns a mask of edges in the depth map.
    Args:
    depth: 2D numpy array of shape (H, W) with dtype float32.
    Returns:
    mask: 2D numpy array of shape (H, W) with dtype bool.
    """
    # Compute the x and y gradients of the depth map.
    depth_dx, depth_dy = np.gradient(depth)
    # Compute the gradient magnitude.
    depth_grad = np.sqrt(depth_dx ** 2 + depth_dy ** 2)
    # Compute the edge mask.
    mask = depth_grad > 0.05
    return mask

def predict_depth(model, image_mesh):
    depth = model.infer_pil(image_mesh)
    return depth

def calculate_free(_free):
    global free
    free = _free
    free -=1
    return free
def calculate_premium(_premium):
    global premium
    premium = _premium
    premium -=1
    return premium



def get_mesh(model, image_mesh, image_texture, keep_edges=False):
    if free == 0 and premium == 0:
        exception()
        return None
    else:
        image_mesh.thumbnail((1024,1024))  # limit the size of the input image_mesh
        depth_mesh = predict_depth(model, image_mesh)
        pts3d_mesh = depth_to_points(depth_mesh[None])
        pts3d_mesh = pts3d_mesh.reshape(-1, 3)

        if free !=0:
            free = calculate_free(free)
        else:
            premium = calculate_premium(premium)

        if image_texture is not None:
            image_texture.thumbnail((1024,1024)) # limit the size of the input image_texture
            depth_texture = predict_depth(model, image_texture)
            pts3d_texture = depth_to_points(depth_texture[None])
            pts3d_texture = pts3d_texture.reshape(-1, 3)
            
 
        set_user_information(id, free, premium)
        # Create a trimesh mesh from the points
        # Each pixel is connected to its 4 neighbors
        # colors are the RGB values of the image

        verts = pts3d_mesh.reshape(-1, 3)
        image_mesh = np.array(image_mesh)
        if image_texture is not None:
            image_texture = np.array(image_texture)

        if keep_edges:
            triangles = create_triangles(image_mesh.shape[0], image_mesh.shape[1])
        else:
            triangles = create_triangles(image_mesh.shape[0], image_mesh.shape[1], mask=~depth_edges_mask(depth_mesh))
        
        if image_texture is not None:
            colors = image_texture.reshape(-1, 3)
        else:
            colors = image_mesh.reshape(-1, 3)
        mesh = trimesh.Trimesh(vertices=verts, faces=triangles, vertex_colors=colors)

        # Save as glb
        glb_file = tempfile.NamedTemporaryFile(suffix='.glb', delete=False)
        glb_path = glb_file.name
        mesh.export(glb_path)
        return glb_path

def exception():
    raise ValueError("You don't have enough credit!")

def getHeaderContent():
    return f"""
        <div style="display: flex; font-size: 30px; justify-content: flex-end;">
            <div>Free: <strong>{free}</strong></div>
            <div style="margin-left: 30px; margin-right: 30px;">Premium: <strong>{premium}</strong></div>
        </div>
        """

def create_demo(model, seafoam):
    global free, premium
    with gr.Blocks(theme=seafoam, css="footer {display: none !important;}") as demo:
        header = gr.HTML(f"""
        <div style="display: flex; font-size: 30px; justify-content: flex-end;">
            <div>Free: <strong>{free}</strong></div>
            <div style="margin-left: 30px; margin-right: 30px;">Premium: <strong>{premium}</strong></div>
        </div>
        """)
    
        with gr.Row():
            image_mesh = gr.Image(label="Input Mesh Image", type='pil')
            image_texture= gr.Image(label="Input Texture Image", type='pil')
            result = gr.Model3D(label="3d mesh reconstruction", clear_color=[
                                                    1.0, 1.0, 1.0, 1.0])
        
        checkbox = gr.Checkbox(label="Keep occlusion edges", value=False)
        submit = gr.Button("Submit", variant="primary")
        submit.click(partial(get_mesh, model), inputs=[image_mesh, image_texture, checkbox ], outputs=[result]).then(
            getHeaderContent, None, header
        )
        examples = gr.Examples(examples=["examples/example1.png", "examples/example2.png", "examples/example3.png", "examples/example4.png", "examples/example5.png"],
                            inputs=[image_mesh])

        demo.load(getHeaderContent, None, header)
    
    return demo
