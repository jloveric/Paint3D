# -*- coding: utf-8 -*-

import time
import torch
from PIL import Image, PngImagePlugin

from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
from diffusers.schedulers import EulerAncestralDiscreteScheduler


class txt2imgControlNet():
    def __init__(self, config, torch_dtype=torch.float16):
        controlnet_list = []
        for cnet_unit in config.controlnet_units:
            controlnet = ControlNetModel.from_pretrained(cnet_unit.controlnet_key, torch_dtype=torch_dtype, resume_download=True)
            controlnet_list.append(controlnet)
        pipe = StableDiffusionControlNetPipeline.from_pretrained(config.sd_model_key, controlnet=controlnet_list,
                                                                 torch_dtype=torch_dtype, resume_download=True).to("cuda")
        pipe.scheduler = EulerAncestralDiscreteScheduler.from_pretrained(config.sd_model_key, subfolder="scheduler", resume_download=True)
        pipe.safety_checker = None
        pipe.feature_extractor = None
        pipe.requires_safety_checker = False
        # pipe.enable_xformers_memory_efficient_attention()
        pipe.enable_model_cpu_offload()
        self.pipe = pipe


    def infernece(self, config):
        """
        :param config: task config for txt2img
        :return:
        """
        w, h = config.width, config.height

        # condition
        control_img = []
        conditioning_scales = []
        for cnet_unit in config.controlnet_units:
            if cnet_unit.preprocessor == 'none':
                condition_image = Image.open(cnet_unit.condition_image_path)
                condition_image = condition_image.resize(size=(w, h), resample=Image.Resampling.BICUBIC)
            else:
                raise NotImplementedError
            control_img.append(condition_image)
            conditioning_scales.append(cnet_unit.weight)
        conditioning_scales = conditioning_scales[0] if len(conditioning_scales) == 1 else conditioning_scales

        seed = int(time.time()) if config.seed == -1 else config.seed
        generator = torch.manual_seed(int(seed))
        res_image = self.pipe(config.prompt,
                              negative_prompt=config.negative_prompt,
                              image=control_img,
                              height=h,
                              width=w,
                              num_images_per_prompt=config.num_images_per_prompt,
                              guidance_scale=config.guidance_scale,
                              num_inference_steps=config.num_inference_steps,
                              generator=generator,
                              controlnet_conditioning_scale=conditioning_scales).images
        return res_image

