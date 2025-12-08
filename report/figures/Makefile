GNUPLOT := `which gnuplot`
EPS2PDF := `which epstopdf`
INKSCAPE := `which inkscape`

GPTFILES = $(wildcard *.gp)
SVGFILES = $(wildcard *.svg)

EPSFILES = $(GPTFILES:%.gp=%.eps) $(wildcard *.eps)
# Convert EPS list to PDF list
PDFFILES_EPS = $(EPSFILES:%.eps=%.pdf)
# Convert SVG list to PDF list
PDFFILES_SVG = $(SVGFILES:%.svg=%.pdf)

PDFFILES = $(PDFFILES_EPS) $(PDFFILES_SVG)

all: $(PDFFILES) Makefile

# Rule for SVG to PDF using Inkscape
# Note: For Inkscape < 1.0, use --export-pdf=$@ instead
%.pdf: %.svg
	$(INKSCAPE) --export-filename=$@ $<

%.pdf: %.eps
	$(EPS2PDF) $*.eps

%.eps: %.gp
	$(GNUPLOT) $*.gp > $*.eps

clean:
	@rm -f $(GPTFILES:%.gp=%.eps)

cleanall:
	@rm -f $(PDFFILES)
