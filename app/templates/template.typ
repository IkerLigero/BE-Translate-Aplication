// Import localization library to handle multi-language PDF generation
#import "@preview/linguify:0.5.0": linguify, set-database

// Define design tokens for brand identity and UI consistency
#let brand-green = rgb("#006450")
#let light-gray = rgb("#f9f9f9")
#let dark-gray = rgb("#4a4a4a")

// Initialize the translation database from the external TOML configuration
#let lang_data = toml("lang.toml")
#set-database(lang_data)

// Capture dynamic parameters passed from the Python backend via CLI inputs
// Default values are provided to ensure document compilation even if data is missing
#let id = sys.inputs.at("id", default: "0")
#let target_lang = sys.inputs.at("target_lang", default: "en")
#let source_lang = sys.inputs.at("source_lang", default: "en")
#let pdf_lang = sys.inputs.at("pdf_lang", default: "en")
#let original_text = sys.inputs.at("original_text", default: "")
#let translated_text = sys.inputs.at("translated_text", default: "")
#let date = sys.inputs.at("date", default: "")
#let user_email = sys.inputs.at("user_email", default: "N/A")

// Configure global page geometry, headers, and footers
#set page(
  paper: "a4",
  margin: (x: 2cm, y: 2.5cm),
  // Persistent header displaying document metadata
  header: align(right)[
    #text(size: 8pt, fill: gray)[#id | #date]
  ],
  // Persistent footer with branding and legal/website links
  footer: [
    #line(length: 100%, stroke: 0.3pt + gray)
    #text(size: 8pt, fill: gray)[CarbonAltDelete - #linguify("title", lang: pdf_lang)]
    #link("https://carbonaltdelete.com")[#h(1fr) carbonaltdelete.com]
  ]
)

// Set base typography rules for the document
#set text(font: "Arial", size: 10pt, lang: pdf_lang, fill: rgb("#333333"))

// --- HEADER SECTION ---
#v(1em) 
#grid(
  columns: (1fr, 1fr), // Split header into title and ID badge
  [
    #text(size: 22pt, weight: "bold", fill: brand-green)[#linguify("title", lang: pdf_lang)]
    #v(-0.5em)
    #text(size: 10pt, fill: dark-gray)[#linguify("report_by", lang: pdf_lang): #strong(user_email)]
  ],
  align(right + bottom)[
    // Styled container for the unique Report ID
    #box(stroke: 1pt + brand-green, inset: 5pt, radius: 2pt)[
      #text(fill: brand-green, weight: "bold")[ID: #id]
    ]
  ]
)

#v(2em)

// --- LANGUAGE METADATA SUMMARY ---
#table(
  columns: (1fr, 1fr),
  stroke: none,
  fill: (x, y) => if y == 0 { light-gray }, // Highlight header row
  [*#linguify("source", lang: pdf_lang)*], [*#linguify("target", lang: pdf_lang)*],
  [#source_lang], [#target_lang]
)

#v(2em)

// --- MAIN CONTENT SECTION ---
#stack(
  spacing: 2em,
  // Source content block (styled with italics for distinction)
  block(width: 100%)[
    #text(fill: brand-green, weight: "bold", size: 11pt)[#linguify("orig_text", lang: pdf_lang)]
    #v(0.5em)
    #block(
      width: 100%, 
      inset: 12pt, 
      radius: 4pt, 
      stroke: 0.5pt + rgb("#e0e0e0")
    )[
      #set text(style: "italic")
      #original_text
    ]
  ],
  
  // Resulting translation block
  block(width: 100%)[
    #text(fill: brand-green, weight: "bold", size: 11pt)[#linguify("trans_res", lang: pdf_lang)]
    #v(0.5em)
    #block(
      width: 100%, 
      fill: light-gray, // Contrast background for translated text
      inset: 12pt, 
      radius: 4pt
    )[
      // Conditional rendering: displays translation or a "pending" status message
      #if translated_text != "" [
        #translated_text
      ] else [
        #text(fill: gray)[#linguify("pending", lang: pdf_lang)]
      ]
    ]
  ]
)

#v(1fr)