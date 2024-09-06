# ChemPerturbDB

## Introduction

ChemPerturbDB is an AI-powered, user-friendly, open-access platform for analyzing Chemical Perturb-Seq (ChemPerturb-Seq) data. ChemPerturb-Seq combines chemical screening with single-cell RNA sequencing (scRNA-seq), offering a systematic analysis of cellular responses and molecular changes in human beta cells following individual hormone treatments.

In this website, users can visualize the expression of genes and enrichment of serveral kinds of pathways.

**Current datasets:**

| Hormones and Growth Factors | Cells |
| --------------------------- | ----- |
| 46                          | 6210  |

Link: [chemperturbdb.weill.cornell.edu](http://chemperturbdb.weill.cornell.edu/)

## Functions

1. Show the violin plot of single gene.
2. Show the dot plot of multiple genes.
3. Show the enrichment of 3 kinds of pathways: beta cell pathways, cell death pathways, specific pathways.
4. Advanced enrichment analysis (the enrichment of customized pathway).

## Usage

### Step 1: prepare the data files

Files needed are listed in [data_files.txt](data_files.txt). But due to size limit, they can't be put here. You can see at [gitlab.com/jtc1246/bio-website](https://gitlab.com/jtc1246/bio-website).

### Step 2: prepare the environment

This website requires these R packages: Seurat, ggplot2, tidyverse, DESeq2, stringr, EnhancedVolcano, pheatmap, RColorBrewer, viridis, grid, ggplotify, ggpubr, patchwork, dplyr, ComplexHeatmap, clusterProfiler, ggh4x. The installation of these R packages will not be described in this README.

You can use the docker at [gitlab.com/jtc1246/bio-website](https://gitlab.com/jtc1246/bio-website).

This website also requires some python packages, which can be installed with:

```bash
pip install myHttp mySecrets myBasics openai PyMuPDF
```

### Step 3: do configurations

1. In [webserver/main.py](webserver/main.py), line 17, set the port you want to use.
2. In [webserver/ai2.py](webserver/ai2.py), line 15, set your OpenAI API key.

### Step 4: run the program

Go to webserver folder, then run:

```bash
python3 main.py
```

Then you can visit the website at `http://127.0.0.1:9020`.
