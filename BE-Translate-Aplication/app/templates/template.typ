#let translation_report(
  id: "",
  source_lang: "",
  target_lang: "",
  original_text: "",
  translated_text: "",
  date: ""
) = {
  set page(paper: "a4", margin: 2cm)
  set text(font: "Arial", size: 11pt)

  // Header
  grid(
    columns: (1fr, 1fr),
    [#text(size: 18pt, weight: "bold")[TMS Report]],
    align(right)[#text(style: "italic")[ID: #id]]
  )

  line(length: 100%, stroke: 0.5pt + gray)
  v(1em)

  // Translation Info
  grid(
    columns: (1fr, 1fr),
    [*Source:* #source_lang],
    [*Target:* #target_lang]
  )
  
  v(2em)

  // Text Blocks
  block(width: 100%, stroke: 0.5pt + luma(200), inset: 10pt, radius: 4pt)[
    #text(weight: "bold")[Original Text:] \
    #original_text
  ]

  v(1em)

  block(width: 100%, fill: luma(240), inset: 10pt, radius: 4pt)[
    #text(weight: "bold")[Translated Result:] \
    #translated_text
  ]

  v(1fr)
  align(bottom + right)[#text(size: 8pt, fill: gray)[Generated on #date]]
}