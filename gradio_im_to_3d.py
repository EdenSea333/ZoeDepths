import gradio as gr
import numpy as np
import trimesh
from geometry import depth_to_points, create_triangles
from functools import partial
import tempfile

free = 2
premium = 0

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

def calculate_free(free):
    free -=1
    return free
def calculate_premium(premium):
    premium -=1
    return premium

def get_mesh(model, image_mesh, image_texture, keep_edges=False):
    global free, premium
    print("-x.l-", free)
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
    global free, premium
    return f"""
        <div style="display: flex; font-size: 30px; justify-content: flex-end;">
            <div>Free: <strong>{free}</strong></div>
            <div style="margin-left: 30px; margin-right: 30px;">Premium: <strong>{premium}</strong></div>
        </div>
        """

def create_demo(model):
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
