# Build the per-configuration CSVs from the archived JSON results (report.py),
# then the long-term trend charts (plot_trends.py) and the HTML gallery (pandoc).

ports=GTK WPE
configs=Release Debug

# CSV per port/config: report.py parses the archived JSON results into one row
# per build. The WPE/GTK x Release/Debug rules are generated below; WPE-ARM64 is
# WPE-only so it is hand-written.
define csv_rule
$(1)-$(2).csv: ../jsonresults/$(1)-Linux-64-bit-$(2)-Tests
	./report.py $$^ -o $$@ --full-parse -c configuration=$1-$2
endef
$(foreach port,$(ports),$(foreach config,$(configs),$(eval $(call csv_rule,$(port),$(config)))))

WPE-ARM64-Release.csv: ../jsonresults/WPE-Linux-ARM64-bit-Release-Tests
	./report.py $^ -o $@ --full-parse -c configuration=WPE-ARM64-Release

STANDARD_CSVS=WPE-Release.csv WPE-Debug.csv WPE-ARM64-Release.csv GTK-Release.csv GTK-Debug.csv
TREND_WINDOWS?=--last 12m
TREND_SMOOTHING?=rolling7d
TREND_REPORT_DIR?=trend-report

# .PHONY is required: `trends` collides with the trends/ package directory, so
# without it make would consider the target already satisfied.
.PHONY: trends trends-legacy trends-html clean

trends: $(STANDARD_CSVS)
	./plot_trends.py $(STANDARD_CSVS) $(TREND_WINDOWS) --smoothing $(TREND_SMOOTHING)

trends-legacy: $(STANDARD_CSVS)
	./plot_trends.py $(STANDARD_CSVS) $(TREND_WINDOWS) --smoothing legacy

# Generate the last-12-months PNGs into trend-report/ and build the gallery HTML
# alongside them (relative image refs, click-through to the originals).
trends-html: $(STANDARD_CSVS)
	mkdir -p $(TREND_REPORT_DIR)
	./plot_trends.py $(STANDARD_CSVS) --last 12m --smoothing rolling7d -d $(TREND_REPORT_DIR)
	pandoc -s -o $(TREND_REPORT_DIR)/chart_details.html \
	  $(TREND_REPORT_DIR)/chart_details.md --section-divs --toc \
	  --metadata date="$$(date +%F)"

clean:
	rm -f *.csv *.png
	rm -f $(TREND_REPORT_DIR)/*.png $(TREND_REPORT_DIR)/chart_details.html
