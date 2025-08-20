from torch.nn.functional import sigmoid
import pandas as pd
import io, os

# ...

all_scores = []
all_labels = []
all_names = []

model.eval()
with torch.no_grad():
    for batch in testLoader:
        images = batch["image"].to(args.local_rank)
        labels = batch["label"].to(args.local_rank)

        # tenta usar um campo de nome/caminho se existir
        if "path" in batch:
            names = batch["path"]
        elif "filename" in batch:
            names = batch["filename"]
        else:
            # fallback: gera IDs automáticos
            names = [f"sample_{len(all_names)+i}" for i in range(len(images))]

        # forward
        logits = model(images)
        probs = sigmoid(logits).cpu().numpy().flatten()

        all_scores.extend(probs.tolist())
        all_labels.extend(labels.cpu().numpy().tolist())
        all_names.extend(names)

# apenas o rank 0 salva o CSV
if rank == 0:
    df = pd.DataFrame({
        "name": all_names,
        "label": all_labels,
        "score": all_scores
    })
    out_csv = os.path.join(args.output_dir if hasattr(args, "output_dir") else ".", "results_per_image.csv")
    df.to_csv(out_csv, index=False)
    logger.info(f"Resultados individuais salvos em {out_csv}")
