mkdir tdps && az storage blob download-batch --pattern "*.pdf" -d tdps -s https://tdps.blob.core.windows.net/tdps