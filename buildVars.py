addon_info = {
	"addon_name": "semanticTree",
	"addon_summary": _("Semantic Tree"),
	"addon_description": _(
		"User-reconfigurable semantic layouts over the NVDA accessibility tree."
	),
	"addon_version": "0.1.0",
	"addon_author": "Kyle Keane <kkeane@mit.edu>",
	"addon_url": "https://github.com/kylekeane/nvda-retree",
	"addon_docFileName": "readme.md",
	"addon_minimumNVDAVersion": "2022.1",
	"addon_lastTestedNVDAVersion": "2024.1",
	"addon_updateChannel": None,
}

pythonSources = ["addon/globalPlugins/semanticTree/*.py", "addon/globalPlugins/semanticTree/ui/*.py"]
i18nSources = pythonSources + ["buildVars.py"]
excludedFiles = []
