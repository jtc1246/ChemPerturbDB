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
require("ggh4x")

library(httpuv) # JTC
library(jsonlite)

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
  tmp<-VlnPlot(exprmatrix, features = geneName, pt.size = 1)+ylab("Normalized Expression")+xlab("Hormone") + theme(legend.position = 'none')+theme(plot.margin = margin(0,0,0,40))
  ggsave(pdf_path, plot = tmp, width=15, height=5)
}

#DotPlot for multiple gene expression, uses data slot from RNA assay in exprmatrix to plot normalized expression of genes (part of Seurat package)
dotPlotMulti<-function(geneNames, pdf_path) {
  features<-strsplit(geneNames, split = ',')[[1]]
  p<-DotPlot(exprmatrix, features = features)
  tmp<-p+coord_flip()+RotatedAxis()+xlab('Gene')+ ylab('Hormone')+guides(color = guide_colorbar(title = "Average(Normalized Expression)"), size="none")+ scale_color_gradientn(
    colors = c("blue", "white", "red"))+theme(plot.margin = margin(0,0,0,20))+theme(aspect.ratio = 0.25)
  ggsave(pdf_path, plot = tmp, width=15, height=7)
}

#Beta cell specific pathways, uses pre-calculated parameters from Betacellspecific.csv file to plot activation/suppression of genes

combinedbetacell["hormone"][combinedbetacell["hormone"] == "Betaestradiol"] <- "Beta-estradiol"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "BrainNeutPeptide"] <- "BNP"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "Growthhormone"] <- "Growth hormone"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "GLP1"] <- "GLP-1"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "IGF1"] <- "IGF-1"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "OrexinA"] <- "Orexin A"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "Seratonin"] <- "Serotonin"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "Pregnenelone"] <- "Pregnenolone"
combinedbetacell["hormone"][combinedbetacell["hormone"] == "PlacentalLactogen"] <- "Placental lactogen"
hormone<-unique(combinedbetacell$hormone)
combinedbetacell$X<-NULL

combinedbetacellsignficant<-subset(combinedbetacell, p.adjust<0.05)
find_missing_hormones <- function(pathway, original_hormones, df) {
  # Subset the dataframe for the specific pathway
  pathway_df <- df %>% filter(Pathways == pathway)
  
  # Find the missing hormones for this pathway
  missing_hormones <- setdiff(original_hormones, pathway_df$hormone)
  
  # Return the missing hormones
  return(missing_hormones)
}
pathways <- unique(combinedbetacellsignficant$Pathways)
missing_hormones_list <- lapply(pathways, find_missing_hormones, hormone, combinedbetacellsignficant)
names(missing_hormones_list) <- pathways

missing_rows <- data.frame()
for (pathway in pathways) {
  # Get the missing hormones for this pathway
  missing_hormones <- missing_hormones_list[[pathway]]
  missing_df <- data.frame(
    ID = pathway,
    Description = pathway,
    setSize=0,
    enrichmentScore=0,
    NES=NA,
    pvalue=0,
    p.adjust=NA,
    qvalue=0,
    rank=0,
    leading_edge=0,
    core_enrichment=0,
    hormone=missing_hormones,
    sign="Activated",
    EnrichementScore=NA,
    Pathways=pathway
  )
  
  missing_rows <- rbind(missing_rows, missing_df)
}

colnames(missing_rows)<-colnames(combinedbetacellsignficant)

combinedbetacellsig <- rbind(missing_rows, combinedbetacellsignficant)

betaPathwaysPlot <- function(zAxisName, pdf_path) {
  Pathway<-combinedbetacellsig[combinedbetacellsig$Pathways == zAxisName, ]
  plot <- ggplot(Pathway, aes(x=hormone,y=Pathways,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0, na.rm=TRUE)+ theme_bw()+ facet_grid(sign~.) + scale_color_gradient(limits=c(0,0.05),low="red", high="blue") + scale_size_continuous(limits = c(0, 3), range = c(0, 3)) + theme(axis.text.x = element_text(angle=90)) +
    force_panelsizes(rows=unit(1,"in") , cols=unit(8, "in"))
  ggsave(pdf_path, plot = plot, width=11, height=6)
  # ??? the pdf size here, the updated code no size, default is 7*7, need to check which to use
}

#Custom cell death pathways, uses pre-calculated parameters from deathpawayenrichment.csv file to plot activation/suppression of genes

combineddeath["hormone"][combineddeath["hormone"] == "Betaestradiol"] <- "Beta-estradiol"
combineddeath["hormone"][combineddeath["hormone"] == "BrainNeutPeptide"] <- "BNP"
combineddeath["hormone"][combineddeath["hormone"] == "Growthhormone"] <- "Growth hormone"
combineddeath["hormone"][combineddeath["hormone"] == "GLP1"] <- "GLP-1"
combineddeath["hormone"][combineddeath["hormone"] == "IGF1"] <- "IGF-1"
combineddeath["hormone"][combineddeath["hormone"] == "OrexinA"] <- "Orexin A"
combineddeath["hormone"][combineddeath["hormone"] == "PlacentalLactogen"] <- "Placental lactogen"
combineddeath["hormone"][combineddeath["hormone"] == "Seratonin"] <- "Serotonin"
combineddeath["hormone"][combineddeath["hormone"] == "Pregnenelone"] <- "Pregnenolone"
hormone<-unique(combineddeath$hormone)
combineddeath$X<-NULL

combineddeathsignficant<-subset(combineddeath, p.adjust<0.05)
find_missing_hormones <- function(pathway, original_hormones, df) {
  # Subset the dataframe for the specific pathway
  pathway_df <- df %>% filter(Pathways == pathway)
  
  # Find the missing hormones for this pathway
  missing_hormones <- setdiff(original_hormones, pathway_df$hormone)
  
  # Return the missing hormones
  return(missing_hormones)
}
pathways <- unique(combineddeathsignficant$Pathways)
missing_hormones_list <- lapply(pathways, find_missing_hormones, hormone, combineddeathsignficant)
names(missing_hormones_list) <- pathways

missing_rows <- data.frame()
for (pathway in pathways) {
  # Get the missing hormones for this pathway
  missing_hormones <- missing_hormones_list[[pathway]]
  missing_df <- data.frame(
    ID = pathway,
    Description = pathway,
    setSize=0,
    enrichmentScore=0,
    NES=NA,
    pvalue=0,
    p.adjust=NA,
    qvalue=0,
    rank=0,
    leading_edge=0,
    core_enrichment=0,
    hormone=missing_hormones,
    sign="Activated",
    EnrichementScore=NA,
    Pathways=pathway
  )
  
  missing_rows <- rbind(missing_rows, missing_df)
}

colnames(missing_rows)<-colnames(combineddeathsignficant)

combineddeathsig <- rbind(missing_rows, combineddeathsignficant)


deathPathwaysPlot <- function(yAxisName, pdf_path) {
  Pathway<-combineddeathsig[combineddeathsig$Pathways == yAxisName, ]
  tmp<-ggplot(Pathway, aes(x=hormone,y=Pathways,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0, na.rm=TRUE)+ theme_bw()+ facet_grid(sign~.) + scale_color_gradient(limits=c(0,0.05),low="red", high="blue") + scale_size_continuous(limits = c(0, 3), range = c(0, 3)) + theme(axis.text.x = element_text(angle=90)) +
  force_panelsizes(rows=unit(1,"in") , cols=unit(8, "in"))
  ggsave(pdf_path, plot = tmp, width=11, height=6)
  # ??? the pdf size here, the updated code no size, default is 7*7, need to check which to use
}

#Specific pathways, uses pre-calculated parameters from GSEAcombined.csv file to plot activation/suppression of genes

combinedpathways["hormone"][combinedpathways["hormone"] == "Betaestradiol"] <- "Beta-estradiol"
combinedpathways["hormone"][combinedpathways["hormone"] == "BrainNeutPeptide"] <- "BNP"
combinedpathways["hormone"][combinedpathways["hormone"] == "Growthhormone"] <- "Growth hormone"
combinedpathways["hormone"][combinedpathways["hormone"] == "GLP1"] <- "GLP-1"
combinedpathways["hormone"][combinedpathways["hormone"] == "OrexinA"] <- "Orexin A"
combinedpathways["hormone"][combinedpathways["hormone"] == "IGF1"] <- "IGF-1"
combinedpathways["hormone"][combinedpathways["hormone"] == "PlacentalLactogen"] <- "Placental lactogen"
combinedpathways["hormone"][combinedpathways["hormone"] == "Seratonin"] <- "Serotonin"
combinedpathways["hormone"][combinedpathways["hormone"] == "Pregnenelone"] <- "Pregnenolone"
hormone<-unique(combinedpathways$hormone)
combinedpathways$X<-NULL

combinedpathwayssignficant<-subset(combinedpathways, p.adjust<0.05)
find_missing_hormones <- function(pathway, original_hormones, df) {
  # Subset the dataframe for the specific pathway
  pathway_df <- df %>% filter(Pathways == pathway)
  
  # Find the missing hormones for this pathway
  missing_hormones <- setdiff(original_hormones, pathway_df$hormone)
  
  # Return the missing hormones
  return(missing_hormones)
}
pathways <- unique(combinedpathwayssignficant$Pathways)
missing_hormones_list <- lapply(pathways, find_missing_hormones, hormone, combinedpathwayssignficant)
names(missing_hormones_list) <- pathways

missing_rows <- data.frame()
for (pathway in pathways) {
  # Get the missing hormones for this pathway
  missing_hormones <- missing_hormones_list[[pathway]]
  missing_df <- data.frame(
    ID = pathway,
    Description = pathway,
    setSize=0,
    enrichmentScore=0,
    NES=NA,
    pvalue=0,
    p.adjust=NA,
    qvalue=0,
    rank=0,
    leading_edge=0,
    core_enrichment=0,
    hormone=missing_hormones,
    sign="Activated",
    EnrichementScore=NA,
    Pathways=pathway
  )
  
  missing_rows <- rbind(missing_rows, missing_df)
}

colnames(missing_rows)<-colnames(combinedpathwayssignficant)

combinedpathwayssig <- rbind(missing_rows, combinedpathwayssignficant)

specificPathwaysPlot <- function(sAxisName, pdf_path) {
 w<-10.25+nchar(sAxisName)*0.06
 Pathway<-combinedpathwayssig[combinedpathwayssig$Pathways == sAxisName, ]
  tmp<-ggplot(Pathway, aes(x=hormone,y=Pathways,color=p.adjust,size=EnrichmentScore), repel=TRUE) + geom_point(alpha=1.0, na.rm=TRUE)+ theme_bw() + facet_grid(sign~.) + scale_color_gradient(limits=c(0,0.05),low="red", high="blue") + scale_size_continuous(limits = c(0, 3), range = c(0, 3)) + theme(axis.text.x = element_text(angle=90)) +  
  force_panelsizes(rows=unit(1,"in") , cols=unit(8, "in"))
  ggsave(pdf_path, plot = tmp, width=w, height=6)  
  # ??? the pdf size here, the updated code no size, default is 7*7, need to check which to use
}


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
    gsea_result <- GSEA(geneList = gene_list, TERM2GENE = gene_sets, minGSSize=5, maxGSSize=500, pvalueCutoff = 1, pAdjustMethod="BH", verbose=TRUE, nPerm=1000)
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
  combined_gsea_df$`Normalized Enrichment Score`<-combined_gsea_df$NES
  combined_gsea_df$sign<-ifelse(combined_gsea_df$sign > 0, "Activated", "Suppressed")
  combined_gsea_df$EnrichmentScore<-abs(combined_gsea_df$NES)
  combined_gsea_df$`-log10(p-value)`<--log10(combined_gsea_df$pvalue)
  
  #Plot enrichment score results
  p<-ggplot(combined_gsea_df, aes(x = `Normalized Enrichment Score`, y = p.adjust, color= hormone, size=`-log10(p-value)`))+geom_point(alpha=1.0)+geom_hline(yintercept = 0.05, color = "black", linetype = "dashed", size = 0.5)+ geom_vline(xintercept = 0, color = "black", linetype = "dashed", size = 0.5)+theme(panel.grid.major = element_blank(), panel.grid.minor = element_blank(),panel.background = element_blank(), axis.line = element_line(colour = "black"))
  tmp<-p+geom_text_repel(aes(label = hormone, segment.color = NA), hjust = -0.3, vjust = 0.5, size = 4)+ guides(color = "none")
  ggsave(pdf_path, plot = tmp, width=12.5,height=6)} 


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
    subset(df, log2FoldChange > 0 & pvalue < 0.1)
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
  # ??? the pdf size here, the updated code no size, default is 7*7, need to check which to use
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