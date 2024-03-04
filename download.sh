#!/bin/bash

# Spécifier le dossier de sortie pour enregistrer les mods téléchargés
output_folder="mods"

# Vider le dossier de sortie s'il existe
rm -rf "$output_folder"
mkdir -p "$output_folder"

wget -P "$output_folder" -i mods_link.txt