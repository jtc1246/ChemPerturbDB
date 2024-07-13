require("Seurat")
require("ggplot2")
require("tidyverse")
require("DESeq2")
require("stringr")
require("EnhancedVolcano")
require("pheatmap")
require("RColorBrewer")
require("viridis")
require("grid")
require("ggplotify")
require("ggpubr")
require("patchwork")
require("dplyr")
require("ComplexHeatmap")
require("clusterProfiler")

library(httpuv) # JTC
library(jsonlite)

# COMMENTED BY JTC
# #Load the matrix for calculating differential gene expression
# endoc<-readRDS("/athena/chenlab/scratch/jjv4001/endocchemperturbnew.RDS")
# #Load the matrix for generating single gene expression and multi-gene dot plot 
# exprmatrix<-readRDS("/athena/chenlab/scratch/jjv4001/exprmatrixmodified.RDS")
# #Set the assay to RNA to access counts in RNA matrix
# DefaultAssay(exprmatrix)<-"RNA"
# #Load the data frame containing pre-calculated results from GSEA to plot enrichment for specific enrichment pathways
# combinedpathways<-read.csv("/athena/chenlab/scratch/jjv4001/GSEAcombined.csv")
# #Load the data frame containing pre-calculated results from GSEA to plot enrichment for cell death associated pathways
# combineddeath<-read.csv("/athena/chenlab/scratch/jjv4001/deathpawayenrichment.csv")
# #Load the data frame containing pre-calculated results from GSEA to plot enrichment for beta cell associated pathways
# combinedbetacell<-read.csv("/athena/chenlab/scratch/jjv4001/Betacellspecific.csv")

# ADDED BY ME
cat("Import Finished\n")
endoc<-readRDS("./endocchemperturbnew.RDS")
# exprmatrix<-readRDS("./exprmatrixmodified.RDS")
exprmatrix<-readRDS("./exprmatrixpseudocount0.1.rds")
DefaultAssay(exprmatrix)<-"RNA"
combinedpathways<-read.csv("./GSEAcombined.csv")
combineddeath<-read.csv("./deathpawayenrichment.csv")
combinedbetacell<-read.csv("./Betacellspecific.csv")
cat("Read File Finished\n")


#Violin Plot for single gene expression, uses data slot from RNA assay in exprmatrix to plot normalized expression of genes (part of Seurat package) 
violinPlotsingle<-function(geneName, pdf_path) {
  expression_matrix <- GetAssayData(exprmatrix, slot = "data")
  maxrowname <- max(expression_matrix[geneName, ])
  # tmp<-VlnPlot(exprmatrix, features = geneName, pt.size = 1)+ylab("Normalized Expression")+xlab("Hormone") + theme(legend.position = 'none')
  # ggsave(pdf_path, plot = tmp, width=15, height=5)
  tmp<-VlnPlot(exprmatrix, features = geneName, pt.size = 1)+ylab("Normalized Expression")+xlab("Hormone") + theme(legend.position = 'none')+theme(plot.margin = margin(0,0,0,40))
  ggsave(pdf_path, plot = tmp, width=10, height=5)
}

#DotPlot for multiple gene expression, uses data slot from RNA assay in exprmatrix to plot normalized expression of genes (part of Seurat package)
dotPlotMulti<-function(geneNames, pdf_path) {
  features<-strsplit(geneNames, split = ',')[[1]]
  p<-DotPlot(exprmatrix, features = features)
  # tmp<-p+coord_flip()+RotatedAxis()+xlab('Gene')+ ylab('Hormone')+guides(color = guide_colorbar(title = 'Normalized Average Expression'))+ scale_color_gradientn(
  #   colors = c("blue", "white", "red"))
  tmp<-p+coord_flip()+RotatedAxis()+xlab('Gene')+ ylab('Hormone')+guides(color = guide_colorbar(title = "Average(Normalized Expression)"), size="none")+ scale_color_gradientn(
    colors = c("blue", "white", "red"))+theme(plot.margin = margin(0,0,0,20))
  ggsave(pdf_path, plot = tmp, width=15, height=7)
}

#Beta cell specific pathways, uses pre-calculated parameters from Betacellspecific.csv file to plot activation/suppression of genes
betaPathwaysPlot <- function(zAxisName, pdf_path) {
  Pathway<-combinedbetacell[combinedbetacell$Pathways == zAxisName, ]
  plot <- ggplot(Pathway, aes(x=hormone,y=Pathways,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0)+ theme_bw()+ facet_grid(sign~.) + scale_color_gradient(low="blue", high="red") + theme(axis.text.x = element_text(angle=90))+ scale_size_continuous(breaks = c(0.4, 0.8, 1.2, 1.6, 2.0))   
  ggsave(pdf_path, plot = plot, width=9, height=6)
}

#Custom cell death pathways, uses pre-calculated parameters from deathpawayenrichment.csv file to plot activation/suppression of genes
deathPathwaysPlot <- function(yAxisName, pdf_path) {
  Pathway<-combineddeath[combineddeath$Pathways == yAxisName, ]
  tmp<-ggplot(Pathway, aes(x=hormone,y=Pathways,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0)+ theme_bw()+ facet_grid(sign~.) + scale_color_gradient(low="blue", high="red") + theme(axis.text.x = element_text(angle=90))+ scale_size_continuous(breaks = c(0.4, 0.8, 1.2, 1.6, 2.0))   
  ggsave(pdf_path, plot = tmp, width=9, height=6)
}

#Specific pathways, uses pre-calculated parameters from GSEAcombined.csv file to plot activation/suppression of genes
specificPathwaysPlot <- function(sAxisName, pdf_path) {
  Pathway<-combinedpathways[combinedpathways$Pathways == sAxisName, ]
  tmp<-ggplot(Pathway, aes(x=hormone,y=Pathways,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0)+ theme_bw() + facet_grid(sign~.) + scale_color_gradient(low="blue", high="red") + theme(axis.text.x = element_text(angle=90))+ scale_size_continuous(breaks = c(0.4, 0.8, 1.2, 1.6, 2.0)) 
  ggsave(pdf_path, plot = tmp, width=9, height=6)  
}

# JTC
# convert_to_named_vector <- function(df, value_var, name_var) {
#   # Ensure the dataframe contains the necessary columns
#   if (!(value_var %in% names(df) && name_var %in% names(df))) {
#     stop("The data frame must contain the specified 'value_var' and 'name_var' columns.")
#   }
#   # Extract the columns as a named vector
#   named_vector <- df[[value_var]]
#   names(named_vector) <- df[[name_var]]
#   return(named_vector)
# }

#customGSEA, input genes as a string, e.g. c("INS", "PDX1", etc.)
# customGSEA<-function(inputgenes,outputfile, pdf_path){
#   genes<-inputgenes
#   nlength<-length(genes)
#   #TERM2GENE, prepare custom geneset using user input genes, geneset requires a 2 column data frame with pathway/term on the left and genes on the right 
#   gene_sets<-data.frame(Term=rep("Custom Gene List", nlength), Gene=genes)
#   #Load our DE lists for GSEA for each hormone into a single list of dataframes
#   directory_path <- "./DElisthormones"
#   csv_files <- list.files(path = directory_path, pattern = "\\.csv$", full.names = TRUE)
#   list_of_data_frames <- lapply(csv_files, read.csv)
#   names(list_of_data_frames) <- tools::file_path_sans_ext(basename(csv_files))
#   #Convert the dataframes into named vectors of decreasing log2foldchange, with genes as names
#   # COMMENT BY JTC object 'convert_to_named_vector' not found
#   convert_to_named_vector <- function(df, value_var, name_var) {
#     vec <- setNames(df[[value_var]], df[[name_var]])
#   }
#   named_vectors_list <- lapply(list_of_data_frames, convert_to_named_vector, value_var = "log2FoldChange", name_var = "Gene")
#   order_named_vector <- function(named_vector) {
#     named_vector[order(-named_vector)]
#   }
#   ordered_named_vectors_list <- lapply(named_vectors_list, order_named_vector)
#   #Run GSEA for each hormone against custom gene list, custom gene list is supplied in TERM2GENE and genelist supplied consists of ordered named numeric vectors and create a list of the GSEA results
#   run_gsea <- function(gene_list, gene_sets) {
#     gsea_result <- GSEA(geneList = gene_list, TERM2GENE = gene_sets, minGSSize=10, maxGSSize=500, pvalueCutoff = 1, pAdjustMethod="BH", verbose=TRUE)
#     return(gsea_result)
#   }
#   gsea_results_list <- lapply(ordered_named_vectors_list, run_gsea, gene_sets = gene_sets)
#   for (i in seq_along(gsea_results_list)) {
#     cat("GSEA Results for Vector", names(ordered_named_vectors_list)[i], ":\n")
#     print(gsea_results_list[[i]])
#   }
#   #convert GSEA list to a dataframe containing GSEA results from all hormones 
#   gsea_to_df <- function(gsea_result, identifier) {
#     df <- as.data.frame(gsea_result)
#     df$hormone <- identifier  # Add an identifier column to track the source of each result
#     return(df)
#   }
#   gsea_dfs <- lapply(seq_along(gsea_results_list), function(i) {
#     gsea_to_df(gsea_results_list[[i]], names(gsea_results_list)[i])
#   })
#   combined_gsea_df <- do.call(rbind, gsea_dfs)
#   write.csv(combined_gsea_df,outputfile)
#   #Create sign column for faceting in ggplot indicating activated or suppressed if NES is above 0 or below 0, create Enrichment Score column with absolute NES and create Pathways column containing ID
#   combined_gsea_df$Pathway<-combined_gsea_df$ID
#   combined_gsea_df$sign<-combined_gsea_df$NES
#   combined_gsea_df$sign<-ifelse(combined_gsea_df$sign > 0, "Activated", "Suppressed")
#   combined_gsea_df$EnrichmentScore<-abs(combined_gsea_df$NES)
#   #Plot enrichment score results
#   tmp<-ggplot(combined_gsea_df, aes(x=hormone,y=Pathway,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0)+ theme_bw()+ facet_grid(sign~.) + scale_color_gradient(low="blue", high="red") + theme(axis.text.x = element_text(angle=90))+ scale_size_continuous(breaks = c(0.4, 0.8, 1.2, 1.6, 2.0))
#   ggsave(pdf_path, plot = tmp, width=9,height=6)} 


#customGSEA, input genes as a string, e.g. c("INS", "PDX1", etc.)
customGSEA<-function(inputgenes,outputfile, pdf_path){
  genes<-inputgenes
  nlength<-length(genes)
  #TERM2GENE, prepare custom geneset using user input genes, geneset requires a 2 column data frame with pathway/term on the left and genes on the right 
  gene_sets<-data.frame(Term=rep("Custom Gene List", nlength), Gene=genes)
  #Load our DE lists for GSEA for each hormone into a single list of dataframes
  directory_path <- "./DElisthormones"
  csv_files <- list.files(path = directory_path, pattern = "\\.csv$", full.names = TRUE)
  list_of_data_frames <- lapply(csv_files, read.csv)
  names(list_of_data_frames) <- tools::file_path_sans_ext(basename(csv_files))
  #Convert the dataframes into named vectors of decreasing log2foldchange, with genes as names
  convert_to_named_vector <- function(df, value_var, name_var) {
    vec <- setNames(df[[value_var]], df[[name_var]])
    sorted_vec <- sort(vec, decreasing = TRUE)
    return(sorted_vec)
  }
  named_vectors_list <- lapply(list_of_data_frames, convert_to_named_vector, value_var = "log2FoldChange", name_var = "Gene")
  order_named_vector <- function(named_vector) {
    named_vector[order(-named_vector)]
  }
  ordered_named_vectors_list <- lapply(named_vectors_list, order_named_vector)
  #Run GSEA for each hormone against custom gene list, custom gene list is supplied in TERM2GENE and genelist supplied consists of ordered named numeric vectors and create a list of the GSEA results
  run_gsea <- function(gene_list, gene_sets) {
    gsea_result <- GSEA(geneList = gene_list, TERM2GENE = gene_sets, minGSSize=5, maxGSSize=500, pvalueCutoff = 1, pAdjustMethod="BH", verbose=TRUE)
    return(gsea_result)
  }
  gsea_results_list <- lapply(ordered_named_vectors_list, run_gsea, gene_sets = gene_sets)
  for (i in seq_along(gsea_results_list)) {
    cat("GSEA Results for Vector", names(ordered_named_vectors_list)[i], ":\n")
    print(gsea_results_list[[i]])
  }
  
  filtered_gsea_results_list <- Filter(function(x) {
    dims <- dim(x)
    !(dims[1] == 0)
  }, gsea_results_list)
  #convert GSEA list to a dataframe containing GSEA results from all hormones 
  gsea_to_df <- function(gsea_result, identifier) {
    df <- as.data.frame(gsea_result)
    df$hormone <- identifier  # Add an identifier column to track the source of each result
    return(df)
  }
  gsea_dfs <- lapply(seq_along(filtered_gsea_results_list), function(i) {
    gsea_to_df(filtered_gsea_results_list[[i]], names(filtered_gsea_results_list)[i])
  })
  combined_gsea_df <- do.call(rbind, gsea_dfs)
  #write.csv(combined_gsea_df,outputfile)
  #Create sign column for faceting in ggplot indicating activated or suppressed if NES is above 0 or below 0, create Enrichment Score column with absolute NES and create Pathways column containing ID
  combined_gsea_df$Pathway<-combined_gsea_df$ID
  combined_gsea_df$sign<-combined_gsea_df$NES
  combined_gsea_df$sign<-ifelse(combined_gsea_df$sign > 0, "Activated", "Suppressed")
  combined_gsea_df$EnrichmentScore<-abs(combined_gsea_df$NES)
  #Plot enrichment score results
  tmp<-ggplot(combined_gsea_df, aes(x=hormone,y=Pathway,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0)+ theme_bw()+ facet_grid(sign~.) + scale_color_gradient(low="blue", high="red") + theme(axis.text.x = element_text(angle=90))+ scale_size_continuous(breaks = c(0.4, 0.8, 1.2, 1.6, 2.0))
  ggsave(pdf_path, plot = tmp, width=9,height=6)} 



#DEG analysis, Volcano Plot and heatmaps for variable genes (users indicate hormone name 1, hormone 2 will be corresponding control which will be pulled from intermediate table), uses endoc seurat object as input and uses the counts slot from the RNA assay
# degAnalysis <- function(hormone1, hormone2, pCutoff, FCcutoff, outputfilepath, pdf_path) {
#   #Choose hormone 1 and subset cells from endoc object to a separate object, create a column in metadata called cell_label to label cell 1 to cell n corresponding to the number of cells in that object
#   H1<-subset(endoc, hormone== hormone1)
#   num_cells_H1 <- ncol(H1)
#   H1$cell_label <- paste0("cell", 1:num_cells_H1)
#   #Choose hormone 2 and subset cells from endoc object to a separate object, create a column in metadata called cell_label to label cell 1 to cell n corresponding to the number of cells in that object
#   H2<-subset(endoc, hormone== hormone2)
#   num_cells_H2 <- ncol(H2)
#   H2$cell_label <- paste0("cell", 1:num_cells_H2)
#   #merge objects to create one count matrix
#   combined<-merge(H1,H2)
#   #run Aggregate expression to perform pseudobulk DE seq, this aggregates counts for all genes according to the groups supplied
#   counts<-AggregateExpression(combined, group.by= c("cell_label","hormone"),slot= "counts", return.seurat = FALSE)
#   counts<-counts$RNA
#   #order columns in counts matrix according to names 
#   suffix <- gsub(".*_", "", colnames(counts))
#   sorted_colnames <- colnames(counts)[order(suffix)]
#   counts <- counts[, sorted_colnames]
#   #create colData corresponding to each cell and hormone to be distinguished (col1=cell1_hormone1, col2=hormone1 or col1=cell100_hormone2, col2=hormone2)
#   colData<-data.frame(samples=colnames(counts))
#   rownames(colData) <- NULL
#   colData$hormone<-gsub('.*_','',colData$samples)
#   colData <- colData %>% 
#     column_to_rownames(var = 'samples')
#   #runDESeq2 analysis
#   dds <- DESeqDataSetFromMatrix(countData = round(counts), colData = colData, design = ~ hormone)
#   keep <- rowSums(counts(dds)) >= 10
#   dds <- dds[keep,]
#   dds<-DESeq(dds)
#   resultsNames(dds)
#   res<-results(dds, pAdjustMethod="BH", contrast=c("hormone",hormone1,hormone2))
#   #remove custom genes corresponding to lentiviral barcoding
#   pattern_to_exclude <- "my.*"
#   res <- res[!grepl(pattern_to_exclude, rownames(res)), ]
#   res <- res[order(res$log2FoldChange, decreasing = TRUE), ]
#   #subset results according to user provided log2foldchange and pvalues
#   res_sig <- subset(res, padj <= pCutoff & abs(log2FoldChange) >= FCcutoff)
#   #create a dataframe containing only the names of the top 10 most significantly upregulated and downregulated genes from the results of DESeq2 
#   res_sig_up <- subset(res_sig, log2FoldChange>0) 
#   res_sig_up <- res_sig_up[order(res_sig_up$log2FoldChange, decreasing = TRUE), ]
#   res_sig_top10 <- (head(rownames(res_sig_up), n = 10)) 
#   res_sig_down <- subset(res_sig, log2FoldChange<0) 
#   res_sig_down <- res_sig_down[order(res_sig_down$log2FoldChange, decreasing = TRUE), ]
#   res_sig_bottom10 <- (tail(rownames(res_sig_down), n = 10))
#   combined_col <- c(res_sig_top10, res_sig_bottom10)
#   combined_col<-unique(combined_col)
#   combined_df <- data.frame(Gene = combined_col)
#   #allow users to save results from DESeq2
#   write.csv(res, outputfilepath)
#   #create volcano plot showing the most signficantly differentially expressed genes 
#   keyvals <- ifelse(
#     res$log2FoldChange < -FCcutoff & res$padj < pCutoff, 'royalblue',
#     ifelse(res$log2FoldChange > FCcutoff & res$padj < pCutoff, 'red',
#            'black'))
#   names(keyvals)[keyvals == 'red'] <- 'Upregulated'
#   names(keyvals)[keyvals == 'royalblue'] <- 'Downregulated'
#   keyvals[is.na(keyvals)] <- 'black'
#   names(keyvals)[keyvals == 'black'] <- 'NS'
#   p1<-EnhancedVolcano(res,
#                       lab = rownames(res),
#                       x = 'log2FoldChange',
#                       y = 'padj',
#                       pCutoff = pCutoff,
#                       FCcutoff = FCcutoff,
#                       colCustom = keyvals,
#                       selectLab = rownames(res_sig),
#                       labSize = 6.0,
#                       labFace = 'bold',
#                       legendLabSize = 14,
#                       legendIconSize = 3.0,
#                       pointSize = 3.0,
#                       boxedLabels = TRUE, drawConnectors = TRUE, gridlines.major = FALSE,
#                       gridlines.minor = FALSE)
#   #perform transformation of dds object and subset vsd to include results of the top 10 most significantly upregulated and downregulated genes and plot heatmap
#   vsd <- varianceStabilizingTransformation(dds)
#   vsd_mat <- assay(vsd)
#   significant_genes<-combined_df$Gene
#   vsd_subset <- subset(vsd_mat, rownames(vsd_mat) %in% significant_genes)
#   custom_colors <- colorRampPalette(brewer.pal(11, "PuOr"))(100)
#   set.seed(1234)
#   plot_2<-ComplexHeatmap::pheatmap(vsd_subset, 
#                    name="Z-score",
#                    cluster_rows = TRUE, 
#                    cluster_cols = FALSE, 
#                    show_rownames = TRUE,
#                    show_colnames = FALSE,
#                    scale="row",
#                    annotation_col = colData,
#                    main = "Heatmap of Top Variable Genes",
#                    fontsize_col = 3, color = custom_colors, cellheight=30)
#   p2<-as.grob(plot_2)
#   #combine enhanced volcano plot and heatmap to display side by side in the same image
#   plots_combined <- wrap_plots(p1, p2, widths = c(1, 1.5))
#   plots_combined
#   ggsave(pdf_path, plot = plots_combined, width=12, height=7)
#   }

visualizeDEResults <- function(resultsFilePath1,resultsFilePath2,resultsFilePath3, pCutoff, FCcutoff,outputfilepath, pdf_path){
  res <- readRDS(resultsFilePath1)
  dds <- readRDS(resultsFilePath2)
  colData <- readRDS(resultsFilePath3)
  # cat("-------------------------------------------------------------")
  # print(class(dds))
  # print(class(res))
  res_sig <- subset(res, padj <= pCutoff & abs(log2FoldChange) >= FCcutoff)
  #create a dataframe containing only the names of the top 10 most significantly upregulated and downregulated genes from the results of DESeq2 
  res_sig_up <- subset(res_sig, log2FoldChange>0) 
  res_sig_up <- res_sig_up[order(res_sig_up$log2FoldChange, decreasing = TRUE), ]
  res_sig_top10 <- (head(rownames(res_sig_up), n = 10)) 
  res_sig_down <- subset(res_sig, log2FoldChange<0) 
  res_sig_down <- res_sig_down[order(res_sig_down$log2FoldChange, decreasing = TRUE), ]
  res_sig_bottom10 <- (tail(rownames(res_sig_down), n = 10))
  combined_col <- c(res_sig_top10, res_sig_bottom10)
  combined_col<-unique(combined_col)
  combined_df <- data.frame(Gene = combined_col)
  #allow users to save results from DESeq2
  write.csv(res, outputfilepath)
  #create volcano plot showing the most signficantly differentially expressed genes 
  keyvals <- ifelse(
    res$log2FoldChange < -FCcutoff & res$padj < pCutoff, 'royalblue',
    ifelse(res$log2FoldChange > FCcutoff & res$padj < pCutoff, 'red',
           'black'))
  names(keyvals)[keyvals == 'red'] <- 'Upregulated'
  names(keyvals)[keyvals == 'royalblue'] <- 'Downregulated'
  keyvals[is.na(keyvals)] <- 'black'
  names(keyvals)[keyvals == 'black'] <- 'NS'
  p1<-EnhancedVolcano(res,
                      lab = rownames(res),
                      x = 'log2FoldChange',
                      y = 'padj',
                      pCutoff = pCutoff,
                      FCcutoff = FCcutoff,
                      colCustom = keyvals,
                      selectLab = rownames(res_sig),
                      labSize = 6.0,
                      labFace = 'bold',
                      legendLabSize = 14,
                      legendIconSize = 3.0,
                      pointSize = 3.0,
                      boxedLabels = TRUE, drawConnectors = TRUE, gridlines.major = FALSE,
                      gridlines.minor = FALSE)
  #perform transformation of dds object and subset vsd to include results of the top 10 most significantly upregulated and downregulated genes and plot heatmap
  cat("Done1")
  vsd <- varianceStabilizingTransformation(dds)
  vsd_mat <- assay(vsd)
  significant_genes<-combined_df$Gene
  vsd_subset <- subset(vsd_mat, rownames(vsd_mat) %in% significant_genes)
  custom_colors <- colorRampPalette(brewer.pal(11, "PuOr"))(100)
  set.seed(1234)
  plot_2<-ComplexHeatmap::pheatmap(vsd_subset, 
                   name="Z-score",
                   cluster_rows = TRUE, 
                   cluster_cols = FALSE, 
                   show_rownames = TRUE,
                   show_colnames = FALSE,
                   scale="row",
                   annotation_col = colData,
                   main = "Heatmap of Top Variable Genes",
                   fontsize_col = 3, color = custom_colors, cellheight=30)
  cat("Done3")
  p2<-as.grob(plot_2)
  #combine enhanced volcano plot and heatmap to display side by side in the same image
  plots_combined <- wrap_plots(p1, p2, widths = c(1, 1.5))
  plots_combined
  ggsave(pdf_path, plot = plots_combined, width=12, height=7)
}

degAnalysis <- function(hormone1, hormone2, pCutoff, FCcutoff, outputfilepath, pdf_path){
  resultsFilePath1 <- paste0('degfiles/',hormone1, 'res.rds')
  resultsFilePath2 <- paste0('degfiles/',hormone1, 'dds.rds')
  resultsFilePath3 <- paste0('degfiles/',hormone1, 'col.rds')
  visualizeDEResults(resultsFilePath1,resultsFilePath2,resultsFilePath3,pCutoff,FCcutoff,outputfilepath, pdf_path)
}

#correlation analysis (heatmap), calculates fraction overlap of user defined genelist and our DE list
correlationAnalysis<-function(genelist, FC, pval, outputfile, pdf_path) {
  #Load list of dataframes corresponding to our DE lists 
  # directory_path <- "/athena/chenlab/scratch/jjv4001/DElisthormones" # ADJUSTED BY ME
  directory_path <- "./DElisthormones" # ADJUSTED BY ME
  csv_files <- list.files(path = directory_path, pattern = "\\.csv$", full.names = TRUE)
  list_of_data_frames <- lapply(csv_files, read.csv)
  names(list_of_data_frames) <- tools::file_path_sans_ext(basename(csv_files))
  #Subset our DE lists to contain genes corresponding to user defined cutoffs of p-values and log2FoldChange
  subset_condition <- function(df) {
    subset(df, log2FoldChange > FC & pvalue < pval)
  }
  subsetted_list <- lapply(list_of_data_frames, subset_condition)
  #Create dataframe of user-defined gene list under the Gene column and find the number of intersecting genes under this column between our lists and user list
  genelist<-data.frame(Gene=genelist)
  find_intersection <- function(genelist, df_other) {
    merge(genelist, df_other, by = "Gene")
  }

  intersection_list <- lapply(subsetted_list, find_intersection, genelist = genelist)
  #find fraction of overlap between our lists and user defined list
  calOverlapFrac <- function(genelist, df_other){
    return(nrow(df_other) / nrow(genelist))
  }
  calOverlapFrac_list <- sapply(intersection_list, calOverlapFrac , genelist = genelist)
  #Create matrix of fraction overlap and plot heatmap
  fracMat <- matrix(calOverlapFrac_list,nrow=1, ncol=45)
  colnames(fracMat) <- names(intersection_list)
  write.csv(fracMat, outputfile)
  tmp<-ComplexHeatmap::pheatmap(fracMat, color=colorRampPalette(c("#4575B4", "#f7f7f7", "#D73027"))(100), name="Fraction Overlap", cluster_rows=F, cluster_cols=F, show_rownames=F, show_colnames=T, fontsize=10, cellheight=50)
  pdf(pdf_path, width=8.5, height=3)
  draw(tmp)
  dev.off()}


# FOLLOWING ADDED BY ME


# violinPlotsingle("INS") # OK
# dotPlotMulti("INS,TOP2A") # OK
# betaPathwaysPlot("Beta Cell Identity") # OK
# deathPathwaysPlot("Ferroptosis Signaling Pathway") # OK
# specificPathwaysPlot("14-3-3-mediated Signaling") # OK
# customGSEA(c("ERO1B","STX1A","EXOC1","PTPRN","EXOC2","PCSK1","PTPRN2","PCSK2","ACVR1C","FFAR1","PCSK1N","RAB27A","P4HB","RAB11B","RIMS2","TMEM27","RAF1","SLC30A5"),"./cgsea_tmp03.csv") # ERROR
# FOR customGSEA, ERROR, object 'convert_to_named_vector' not found
# degAnalysis("LPT", "endoc3BC3", 0.05, 0.5, "./deg_tmp01.csv") # OK 需要注意最后一个参数是输出路径 不是输入
# correlationAnalysis(c("ERO1B","STX1A","EXOC1","PTPRN","EXOC2","PCSK1","PTPRN2","PCSK2","ACVR1C","FFAR1","PCSK1N","RAB27A","P4HB","RAB11B","RIMS2","TMEM27","RAF1","SLC30A5"), 0, 0.1, "./correlation_tmp02.csv") # OK 也要注意是输出路径






hex_to_string <- function(hex_str) {
  # 将十六进制字符串分割成每两个字符一组
  hex_split <- strsplit(hex_str, "(?<=..)", perl = TRUE)[[1]]
  # 将每个十六进制字符转换为整数，然后转换为字符
  raw_vec <- as.raw(as.hexmode(hex_split))
  # 将原始字节序列转换为字符串
  result_str <- rawToChar(raw_vec)
  return(result_str)
}

cat(hex_to_string("48656c6c6f20576f726c6421"), "\n")



app <- list(
  call = function(req) {
    url <- req$PATH_INFO
    json_data <- hex_to_string(substr(url, 2, nchar(url)))
    data <- fromJSON(json_data)

    f <- data$f
    if(f == 1){
      cat('violinPlotsingle', "\n")
      violinPlotsingle(data$p1, data$p6)
    }
    if(f == 2){
      cat('dotPlotMulti', "\n")
      dotPlotMulti(data$p1, data$p6)
    }
    if(f == 3){
      cat('betaPathwaysPlot', "\n")
      betaPathwaysPlot(data$p1, data$p6)
    }
    if(f == 4){
      cat('deathPathwaysPlot', "\n")
      deathPathwaysPlot(data$p1, data$p6)
    }
    if(f == 5){
      cat('specificPathwaysPlot', "\n")
      specificPathwaysPlot(data$p1, data$p6)
    }
    if(f == 6){
      cat('customGSEA', "\n")
      customGSEA(data$p1, data$p2, data$p6)
    }
    if(f == 7){
      cat('degAnalysis', "\n")
      degAnalysis(data$p1, data$p2, data$p3, data$p4, data$p5, data$p6)
    }
    if(f == 8){
      cat('correlationAnalysis', "\n")
      correlationAnalysis(data$p1, data$p2, data$p3, data$p4, data$p6)
    }

    # 构建响应体
    response_body <- paste0("finished")

    # 返回响应
    return(list(
      status = 200L,
      headers = list(
        'Content-Length' = '8'
      ),
      body = response_body
    ))
  }
)


server <- startServer("0.0.0.0", 2000, app)
cat("Server started on http://localhost:2000\n")

# 保持事件循环
while(TRUE) {
  service()
  Sys.sleep(0.001)
}





while(TRUE) {
  service()
  Sys.sleep(0.001)
}