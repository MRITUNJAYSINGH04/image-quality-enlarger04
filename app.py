import spaces
import gradio as gr
from gradio_imageslider import ImageSlider
from PIL import Image
import numpy as np
from aura_sr import AuraSR
import torch
import time
import spaces

# Force CPU usage
torch.set_default_tensor_type(torch.FloatTensor)

# Override torch.load to always use CPU
original_load = torch.load
torch.load = lambda *args, **kwargs: original_load(*args, **kwargs, map_location=torch.device('cpu'))

# Initialize the AuraSR model
aura_sr = AuraSR.from_pretrained("fal/AuraSR-v2")

# Restore original torch.load
torch.load = original_load

def process_image(input_image, scale_factor):
    if input_image is None:
        raise gr.Error("Please provide an image to upscale.")

    start_time = time.time()

    # Convert to PIL Image for resizing
    pil_image = Image.fromarray(input_image)

    if scale_factor == 2:
        pil_image = pil_image.resize((int(pil_image.width * 0.5), int(pil_image.height * 0.5)), Image.LANCZOS)
    elif scale_factor == 3:
        pil_image = pil_image.resize((int(pil_image.width * 0.75), int(pil_image.height * 0.75)), Image.LANCZOS)

    # Upscale the image using AuraSR
    upscaled_image = process_image_on_gpu(pil_image)

    # Convert result to numpy array if it's not already
    result_array = np.array(upscaled_image)

    end_time = time.time()
    processing_time = end_time - start_time

    return [input_image, result_array], f"Processing time: {processing_time:.2f} seconds"

@spaces.GPU
def process_image_on_gpu(pil_image):
    try:
        return aura_sr.upscale_4x(pil_image)
    except Exception as e:
        raise gr.Error(f"An error occurred during image upscaling: {str(e)}")

with gr.Blocks() as demo:
    gr.Markdown("# Image Upscaler")
    with gr.Row():
        input_image = gr.Image(label="Input Image", type="numpy")
        scale_factor = gr.Radio([2, 3, 4], label="Scale Factor", value=4)
    with gr.Row():
        image_slider = ImageSlider(label="Before/After")
    upscale_button = gr.Button("Upscale")
    processing_time_text = gr.Textbox(label="Processing Time")
    upscale_button.click(fn=process_image, inputs=[input_image, scale_factor], outputs=[image_slider, processing_time_text])

demo.launch()
