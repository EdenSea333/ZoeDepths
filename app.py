from __future__ import annotations
from typing import Iterable
import gradio as gr
from gradio.themes.base import Base
from gradio.themes.utils import colors, fonts, sizes
from gradio_im_to_3d import create_demo as create_im_to_3d_demo
import torch

DEVICE = 'cuda' if torch.cuda.is_available() else 'cpu'
model = torch.hub.load('isl-org/ZoeDepth', "ZoeD_N", pretrained=True).to(DEVICE).eval()

class Seafoam(Base):
    def __init__(
        self,
        *,
        primary_hue: colors.Color | str = colors.emerald,
        secondary_hue: colors.Color | str = colors.red,
        neutral_hue: colors.Color | str = colors.blue,
        spacing_size: sizes.Size | str = sizes.spacing_md,
        radius_size: sizes.Size | str = sizes.radius_md,
        text_size: sizes.Size | str = sizes.text_lg,
        font: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("Quicksand"),
            "ui-sans-serif",
            "sans-serif",
        ),
        font_mono: fonts.Font
        | str
        | Iterable[fonts.Font | str] = (
            fonts.GoogleFont("IBM Plex Mono"),
            "ui-monospace",
            "monospace",
        ),
    ):
        super().__init__(
            primary_hue=primary_hue,
            secondary_hue=secondary_hue,
            neutral_hue=neutral_hue,
            spacing_size=spacing_size,
            radius_size=radius_size,
            text_size=text_size,
            font=font,
            font_mono=font_mono,
        )
        super().set(
            body_text_color="#FFFFFF",
            body_background_fill="#FF0064",
            block_background_fill="#1C1C1C",
            block_label_text_color="#FFFFFF",
            block_label_background_fill="#2C2C2C",
            block_border_color="#00000000",
            button_primary_background_fill="#1C1C1C",
            button_primary_text_color="#FFFFFF",
            error_background_fill="#1C1C1C",
            error_border_color="#FFFFFF",
            error_text_color="#FFFFFF",
            checkbox_label_border_color="#FF0000",
            checkbox_background_color="#FFFFFF",
            border_color_primary="#2C2C2C",
            background_fill_primary="#111111",
            button_secondary_border_color="#111111",
        )

seafoam = Seafoam()
with gr.Blocks(theme=seafoam) as demo:
    create_im_to_3d_demo(model)
demo.launch(share=True, server_name="0.0.0.0")