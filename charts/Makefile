
ports=GTK WPE
configs=Release Debug

all: plot_GTK_Release plot_GTK_Debug plot_WPE_Release plot_WPE_Debug

define set_targets
$(1)-$(2).csv: ../jsonresults/$(1)-Linux-64-bit-$(2)-Tests
	./report.py $$^ -o $$@

plot_$(1)_$(2): $(1)-$(2).csv
	./plot.py -p $(1) -c $(2) $$^
endef

$(foreach port,$(ports),$(foreach config,$(configs),$(eval $(call set_targets,$(port),$(config)))))

clean:
	rm -f *.csv
	rm -f *.png
