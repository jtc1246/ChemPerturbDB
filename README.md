# ChemicalDB

## Introduction

This a website that allows users to visualize the expression of genes and enrichment of serveral kinds of pathways. ChemicalDB contains single cell RNA sequencing (scRNAseq) data from the EndoC-βH1 cell line, an immortalized human β-cell line, treated with 46 different hormones from our in-house hormone screening library.

**Current datasets:**

| Hormones and Growth Factors | Genes | Cells |
| --------------------------- | ----- | ----- |
| 46                          | 36627 | 6210  |

Link for demo: [jtc1246.com:9020](http://jtc1246.com:9020/)

## Functions

1. Show the violin plot of single gene.
2. Show the dot plot of multiple genes.
3. Show the enrichment of 4 kinds of pathways: beta cell pathways, cell death pathways, specific pathways, and customized pathways combined with a set of genes.
4. DEG analysis of hormones. (this may be changed later)
5. Correlation analysis of genes.

## Usage

### Step 1: prepare the data files

Files needed are listed in [data_files.txt](data_files.txt). But due to size limit, they can't be put here. You can see at [gitlab.com/jtc1246/bio-website](https://gitlab.com/jtc1246/bio-website).

### Step 2: prepare the environment

This website requires these R packages: Seurat, ggplot2, tidyverse, DESeq2, stringr, EnhancedVolcano, pheatmap, RColorBrewer, viridis, grid, ggplotify, ggpubr, patchwork, dplyr, ComplexHeatmap, clusterProfiler. The installation of these R packages will not be described in this README.

You can use the docker at [gitlab.com/jtc1246/bio-website](https://gitlab.com/jtc1246/bio-website).

This website also requires some python packages, which can be installed with:

```bash
pip install myHttp mySecrets myBasics openai PyMuPDF
```

### Step 3: Do configurations

1. In [webserver/main.py](webserver/main.py), line 17, set the port you want to use.
2. In [webserver/ai2.py](webserver/ai2.py), line 15, set your OpenAI API key.

### Step 4: Run the program

Go to webserver folder, then run:

```bash
python3 main.py
```

Then you can visit the website at `http://127.0.0.1:9020`.
