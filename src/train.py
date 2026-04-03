import os
import pandas as pd
from datasets import Dataset
from transformers import (
    DistilBertTokenizerFast,
    DistilBertForSequenceClassification,
    Trainer,
    TrainingArguments,
    DataCollatorWithPadding
)

print("Training script started.")

# Setting up absolute paths based on the new /src/ location
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Go up one level from 'src', then into 'data' and 'models'
DATA_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "data"))
MODEL_DIR = os.path.abspath(os.path.join(BASE_DIR, "..", "models", "classifier_model"))

os.makedirs(MODEL_DIR, exist_ok=True)
# Load data
def load_list(filename):
    with open(os.path.join(DATA_DIR, filename), "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

benign = load_list("benign.txt")
malicious = load_list("malicious.txt")
jailbreak = load_list("jailbreak.txt")

print("Counts -> Benign:", len(benign), "Malicious:", len(malicious), "Jailbreak:", len(jailbreak))

# Create DataFrame
df = pd.DataFrame({
    "text": benign + malicious + jailbreak,
    "labels": [0]*len(benign) + [1]*len(malicious) + [2]*len(jailbreak)
})

# Convert to dataset
dataset = Dataset.from_pandas(df)

tokenizer = DistilBertTokenizerFast.from_pretrained("distilbert-base-uncased")

def tokenize(batch):
    return tokenizer(batch["text"], truncation=True)

dataset = dataset.map(tokenize, batched=True)

# ❗ REMOVE ALL NON-TENSOR FRIENDLY COLUMNS
dataset = dataset.remove_columns(["text"])

# Add padding dynamically
data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Load model
model = DistilBertForSequenceClassification.from_pretrained(
    "distilbert-base-uncased",
    num_labels=3
)

training_args = TrainingArguments(
    output_dir="./results",
    num_train_epochs=3,
    per_device_train_batch_size=8,
    logging_steps=10,
    remove_unused_columns=False  # IMPORTANT
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=dataset,
    data_collator=data_collator,
    processing_class=tokenizer  # <--- This is the new way!
)

trainer.train()

model.save_pretrained(MODEL_DIR)
tokenizer.save_pretrained(MODEL_DIR)

print("Training complete!")