#import "@preview/linguify:0.5.0": linguify, set-database

// Load the TOML
#let lang_data = toml("lang.toml")
#set-database(lang_data)

// Python inputs from command line
#let id = sys.inputs.at("id", default: "0")
#let target_lang = sys.inputs.at("target_lang", default: "en")
#let source_lang = sys.inputs.at("source_lang", default: "en")
#let pdf_lang = sys.inputs.at("pdf_lang", default: "en")
#let original_text = sys.inputs.at("original_text", default: "")
#let translated_text = sys.inputs.at("translated_text", default: "")
#let date = sys.inputs.at("date", default: "")
#let user_email = sys.inputs.at("user_email", default: "N/A")

// Text and language configuration
#set page(paper: "a4", margin: 2cm)
// Set text properties: 'lang' uses pdf_lang for static labels and general document locale
#set text(font: "Arial", size: 11pt, lang: pdf_lang) 

// --- DESIGN ---
#grid(
  columns: (1fr, 1fr),
  [#text(size: 18pt, weight: "bold")[#linguify("title", lang: pdf_lang)]],
  align(right)[
    #text(style: "italic")[ID: #id] \
    #text(size: 9pt)[#linguify("report_by", lang: pdf_lang): #user_email] // <--- LÍNEA NUEVA
  ]
)

#line(length: 100%, stroke: 0.5pt + gray)
#v(1em)

#grid(
  columns: (1fr, 1fr),
  [*#linguify("source", lang: pdf_lang):* #source_lang],
  [*#linguify("target", lang: pdf_lang):* #target_lang]
)

#v(2em)

#block(width: 100%, stroke: 0.5pt + luma(240), inset: 10pt, radius: 4pt)[
  #text(weight: "bold")[#linguify("orig_text", lang: pdf_lang)] \
  #original_text
]

#v(1em)

#block(width: 100%, fill: luma(245), inset: 10pt, radius: 4pt)[
  #text(weight: "bold")[#linguify("trans_res", lang: pdf_lang)] \
  #if translated_text != "" [#translated_text] else [#linguify("pending", lang: pdf_lang)]
]

#v(1fr)
#align(bottom + right)[#text(size: 8pt, fill: gray)[#linguify("gen_on", lang: pdf_lang) #date]]