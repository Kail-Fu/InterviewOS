# Assessment 4 Test Data

## Required Files

Place the following test data files in this directory:

1. **product_ner_test_id.jsonl** - In-domain test set (visible to candidates)
2. **product_ner_test_ood.jsonl** - Out-of-domain test set (hidden, for final evaluation)

## File Format

Each line should be a JSON object with:
```json
{
  "tokens": ["Nike", "Air", "Max", "shoes"],
  "ner_tags": ["B-BRAND", "I-BRAND", "I-BRAND", "B-TYPE"]
}
```

## Label Set

Expected NER tags:
- O (outside)
- B-BRAND, I-BRAND
- B-COLOR, I-COLOR
- B-TYPE, I-TYPE
- B-SIZE, I-SIZE
- B-MATERIAL, I-MATERIAL
- B-GENDER, I-GENDER

