#!/bin/bash

INPUT_FILE="addresses.csv"
OUTPUT_FILE="output_results.json"

echo "[" > $OUTPUT_FILE
first_row=true

while IFS= read -r address || [ -n "$address" ]; do
  if [ -z "$address" ]; then
    continue
  fi

  echo "Processing: $address"

  if [ "$first_row" = false ]; then
    echo "," >> $OUTPUT_FILE
  fi
  first_row=false

  # တိကျပြီး အသိဉာဏ်သုံးခိုင်းထားသော စည်းကမ်းချက်အသစ်များ
  llm -m openrouter/google/gemini-2.5-flash "You are an expert Myanmar Address Parser. Analyze the address string carefully and extract each component into JSON format.

CRITICAL RULES:
1. OUTPUT ONLY RAW JSON. No markdown code blocks (No \`\`\`), no explanations.
2. If any field is missing, strictly use 'N/A'.
3. Do NOT mix fields (e.g., 'ward' and 'village' must be separate).
4. Use logical inference for incomplete addresses (e.g., If it says 'နေပြည်တော်', the city is 'နေပြည်တော်' and division_state is 'နေပြည်တော် ပြည်ထောင်စုနယ်မြေ'. If it says 'လျှပ်စစ်', interpret it intelligently as street or landmark).
5. Convert short-form townships to full names (e.g., 'တ/ဥ' -> 'တောင်ဥက္ကလာပမြို့နယ်').

Address: '$address'

{
  \"home_no\": \"အိမ်အမှတ် သို့မဟုတ် တိုက်အမှတ် သာထည့်ရန်\",
  \"floor_room\": \"အလွှာ သို့မဟုတ် အခန်းအမှတ် သာထည့်ရန်\",
  \"street_landmark\": \"လမ်းအမည် သို့မဟုတ် အနီးနားနေရာအမှတ်အသား သာထည့်ရန်\",
  \"ward\": \"ရပ်ကွက်အမည် သာထည့်ရန် (ကျေးရွာမပါရ)\",
  \"village\": \"ကျေးရွာအမည် သာထည့်ရန် (ရပ်ကွက်မပါရ)\",
  \"township\": \"မြို့နယ်အမည်အပြည့်အစုံ သာထည့်ရန်\",
  \"city\": \"မြို့အမည် သာထည့်ရန်\",
  \"division_state\": \"တိုင်းဒေသကြီး သို့မဟုတ် ပြည်နယ်အမည် သာထည့်ရန်\"
}" -o max_tokens 1000 >> $OUTPUT_FILE

done < $INPUT_FILE

echo "]" >> $OUTPUT_FILE
echo "ပြီးပါပြီ။ ညွှန်ကြားချက်အသစ်ဖြင့် $OUTPUT_FILE ထဲတွင် ပြန်လည်သိမ်းဆည်းလိုက်ပါပြီ။"
