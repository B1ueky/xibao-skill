---
name: xibao-poster
description: |
  Generate 喜报 (celebration posters) and 海报 (advertising posters) for a visa/immigration consultancy.
  Use this skill whenever the user provides visa grant letters (下签信), customer chat screenshots, or says things like "做喜报", "生成喜报", "做海报", "帮我做一张", or asks to process visa approval images into celebration posters.

  This skill handles TWO poster types:
  - **Visa Grant Poster (下签喜报)**: Takes an Australian visa grant letter image → produces a festive red/gold 喜报 with annotation, watermark, arrows, and decorations.
  - **Chat Advertising Poster (聊天宣传海报)**: Takes a WeChat screenshot → produces an advisory poster with top text, chat screenshot, and annotation.

  Output: 1200×1800px JPEG at 80 DPI. Uses Python/Pillow — no Canva required. Always use this skill when the user wants to produce 喜报 or 海报 from visa letters or chat screenshots.
---

# 喜报海报生成技能 (Xibao Poster Generator)

This skill automates the creation of celebration posters (喜报) and advertising posters (海报) for a visa/immigration consultancy business. It reads visa grant letters and WeChat screenshots, extracts the relevant information, and generates festive, professional posters.

---

## Workflow Overview

1. **Read and analyse all input images** in the user's folder
2. **Extract key information** from each visa letter or chat screenshot
3. **Determine the annotation text** (Chinese summary of the visa outcome)
4. **Generate posters** using the bundled Python script
5. **Save and present** the output files to the user

---

## Step 1 — Identify Input Materials

Read every image file the user provides or points to. Look for:

- **Visa grant letters**: Australian Government, Department of Home Affairs letterhead. Fields to find:
  - Applicant name (e.g., "Dear ___ XUE")
  - Visa type (e.g., "Visitor (subclass 600)")
  - Date of grant
  - Stay until / Must not arrive after (determines validity end)
  - Length of stay (e.g., "29 April 2026" = fixed; "12 month(s) from date of each arrival" = rolling)
  - Travel: "Multiple entries" or "Single entry"

- **WeChat / chat screenshots**: Conversation images showing grant notifications and client reactions

- **Poster type to produce**: Ask the user if unclear, or infer from context:
  - Visa letter → "visa" poster
  - Chat screenshot → "chat" poster

---

## Step 2 — Prepare Visa Poster Text Fields

For the new design, read the visa letter carefully and prepare these texts:

### `--title` (3-line congratulatory heading, white on red)
Customise per case. Use `\n` to separate up to 3 lines:
```
"澳洲新传奇恭喜X女士\n一家六口澳洲旅游签\n一周光速下签！"
```

### `--visa-number` (family member counter on visa letter)
Which family member this visa letter belongs to. Use circled numbers:
`①` `②` `③` `④` `⑤` `⑥` (or plain digits `1` `2` `3` etc.)

### `--description` (case detail lines, cream text below title)
Short summary lines. Use `\n` to separate:
```
"案例特点：W女士全家从未申请过澳洲签证，拒签率高\n递签时间：2024年2月19日\n获批时间：2024年2月27日"
```

### `--story-text` (diagonal red text overlaid on visa letter)
One flowing paragraph about the case (auto-wraps at ~18 chars/line, auto-rotated -15°):
```
"客户有他国旅行记录，找到新传奇帮忙递签，准备资料时新传奇突出客户稳定的收入以及多国良好旅行记录的优势，帮全家申请获得1年多次往返澳洲旅游签证！"
```

### For Chat Advertising Poster — `--annotation`
The large quote text overlaid on the chat screenshot (e.g. `"客户希望今天就下签！结果真的如他所愿"`).

---

## Step 3 — Generate the Poster

Run the bundled script. The script is at:
```
scripts/generate_poster.py
```

### Visa Grant Poster (下签喜报)
```bash
python3 "{{SKILL_DIR}}/scripts/generate_poster.py" \
  --input  "/path/to/visa_letter.png" \
  --output "/path/to/output_poster.jpg" \
  --type   visa \
  --title  "澳洲新传奇恭喜X女士\n一家六口澳洲旅游签\n一周光速下签！" \
  --description "案例特点：全家首次申请，拒签率高\n递签时间：2024年2月19日\n获批时间：2024年2月27日" \
  --visa-number "①" \
  --story-text "客户有他国旅行记录，找到新传奇帮忙递签，准备资料时新传奇突出客户稳定的收入以及多国良好旅行记录的优势，帮全家申请获得1年多次往返澳洲旅游签证！" \
  --month  "2月" \
  --year   "2024"
```

### Chat Advertising Poster (宣传海报)
```bash
python3 "{{SKILL_DIR}}/scripts/generate_poster.py" \
  --input    "/path/to/chat_screenshot.png" \
  --output   "/path/to/output_poster.jpg" \
  --annotation "客户希望今天就下签！结果真的如他所愿" \
  --type     chat \
  --top-text "目前旅游签证审理严格，特别是经济收入方面的材料，务必提交齐全，以免造成拒签。"
```

### All arguments
| Argument | Description |
|---|---|
| `--input` | Path to the source image (visa letter or chat screenshot) |
| `--output` | Destination path for the output JPG |
| `--type` | `visa` or `chat` |
| `--title` | Visa: 3-line white heading (use `\n` between lines) |
| `--description` | Visa: case detail lines (use `\n` between lines) |
| `--visa-number` | Visa: family member counter (e.g. `①`, `②`, `1`, `2`) |
| `--story-text` | Visa: diagonal story paragraph on the letter |
| `--annotation` | Visa: alternate overlay text; Chat: quote annotation |
| `--month` | Month for subtitle/description (e.g. `2月`) |
| `--year` | Year for subtitle/description (e.g. `2024`) |
| `--top-text` | Chat poster only: advisory paragraph in yellow box |
| `--watermark-image` | Path to a PNG logo (with transparency) for watermark |

---

## Step 4 — Batch Processing

When the user provides multiple visa letters (e.g., customer1 info.png … customer6 info.png), process them all. Read each letter, determine the annotation, and generate a poster for each one.

Save all output files to the user's mounted folder (the "advertising poster generator" folder or wherever they specify).

Name the output files descriptively:
- `喜报_Customer1_五年多次往返.jpg`
- `喜报_Customer2_一个月旅游签.jpg`
- `海报_聊天截图_宣传.jpg`

---

## Design Reference

### Visa Grant Poster (下签喜报) — new template
- **Background**: Deep red (#B90F0F area)
- **Top band**: Gold 祥云 wave band with cloud-puff decorations + scalloped bottom edge
- **Bottom band**: Gold 祥云 wave band (scalloped top edge)
- **Title**: 3 lines of large **white** bold text on red (no box) — customisable
- **Description**: 3–4 lines of warm cream text (case details, dates)
- **梅花**: Red plum blossom decoration to the right of description
- **Visa letter**: Embedded centrally, occupying ~60% of poster height
- **旅游签N overlay**: Large red text centered on upper portion of letter (N = family member)
- **Story text**: Diagonal red paragraph at –15°, white stroke outline, across lower letter
- **Watermark**: Golden 3-line New Legend tile across the letter
- **Top-right**: 贺 badge PNG (gold cog + ribbon design)
- **Bottom-left**: Fireworks / sparkle decorations

### Chat Advertising Poster (宣传海报)
- **Background**: Deep red (#B91212)
- **Border**: Golden yellow strips with red scallop punch-outs + gold inner line
- **Top box**: Yellow rounded rectangle with large black advisory text (font 54)
- **Top-right of box**: Simple cartoon traveller with luggage
- **Chat screenshot**: Full WeChat conversation, centred below text box, gold border
- **Watermark**: Golden 3-line New Legend tile on chat screenshot
- **Annotation**: Large red text (font 58) **overlaid** at ≈42% from top of chat image, with white stroke outline
- **Arrows**: Two red curved arrows from annotation pointing **down** toward PDF attachments (≈72% from top of chat)
- **Top-right**: Ornate gold medallion `贺` badge
- **Bottom-left**: Firework decorations

### Output
1200×1800 JPEG @ 80 DPI

---

## Using Your Company Watermark

To use the New Legend watermark logo instead of plain text:

1. Open your Canva design at https://www.canva.com/design/DAF0wE0xeEw/...
2. Select just the watermark element → right-click → **Download as PNG** with transparent background
3. Save the PNG file into your working folder (e.g., `watermark_logo.png`)
4. Add `--watermark-image "/path/to/watermark_logo.png"` to the generate command

The script will tile the logo across the embedded image at 25% opacity.

---

## Tips for Best Results

- Always read the visa letter image carefully before setting `--annotation` — the key data is in "Visa duration and travel" and "Length of stay" sections.
- The subtitle month/year should match the grant date from the letter (e.g., a March 2026 grant → `--month "3月" --year "2026"`).
- For chat posters, `--top-text` wraps at ~18 chars/line; aim for 2–4 lines.
- Annotation text is auto-wrapped so it always fits within the image.
- If there are both visa letters AND chat screenshots, generate both types and present them together.
- After generating, always present the output files to the user using `mcp__cowork__present_files`.