from transformers import AutoModelForCausalLM

class CustomModel(AutoModelForCausalLM):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if hasattr(self.config, 'rope_scaling'):
            self.config.rope_scaling['name'] = 'default'  # ou outro valor apropriado

model = CustomModel.from_pretrained(
    args.model_name_or_path,
    cache_dir=args.cache_dir,
    load_in_4bit=args.bits == 4,
    load_in_8bit=args.bits == 8,
    device_map=device_map,
    max_memory=max_memory,
    quantization_config=BitsAndBytesConfig(
        load_in_4bit=args.bits == 4,
        load_in_8bit=args.bits == 8,
        llm_int8_threshold=6.0,
        llm_int8_has_fp16_weight=False,
        bnb_4bit_compute_dtype=compute_dtype,
        bnb_4bit_use_double_quant=args.double_quant,
        bnb_4bit_quant_type=args.quant_type,
    ),
    torch_dtype=(torch.float32 if args.fp16 else (torch.bfloat16 if args.bf16 else torch.float32)),
    trust_remote_code=args.trust_remote_code,
    use_auth_token=args.use_auth_token
)
