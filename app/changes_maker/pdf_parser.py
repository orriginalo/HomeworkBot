import camelot

# PDF file to extract tables from
file = "./app/changes_maker/test.pdf"
tables = camelot.read_pdf(file)