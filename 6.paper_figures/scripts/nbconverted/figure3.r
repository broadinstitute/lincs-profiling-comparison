suppressPackageStartupMessages(library(dplyr))
suppressPackageStartupMessages(library(ggplot2))
suppressPackageStartupMessages(library(patchwork))
suppressPackageStartupMessages(library(ComplexHeatmap))

source("viz_themes.R")
source("plotting_functions.R")
source("data_functions.R")

output_figure_base <- file.path("figures", "figure3")
extensions <- c(".png", ".pdf")

results_dir <- file.path("../1.Data-exploration/Profiles_level4/")

cp_df <- load_embeddings_data(assay="cellpainting", results_dir = results_dir)
l1000_df <- load_embeddings_data(assay="l1000", results_dir = results_dir)

# Create compounds to highlight
moa_targets_size_values <- c(rep(1, length(moa_targets) -1), 0.1)
names(moa_targets_size_values) <- names(moa_targets)

moa_targets_alpha_values <- c(rep(0.5, length(moa_targets) - 1), 0.1)
names(moa_targets_alpha_values) <- names(moa_targets)

cp_df <- cp_df %>% dplyr::mutate(highlight_moa = tolower(moa))
cp_df$highlight_moa[!(cp_df$highlight_moa %in% names(moa_targets))] <- "other"

l1000_df <- l1000_df %>% dplyr::mutate(highlight_moa = tolower(moa))
l1000_df$highlight_moa[!(l1000_df$highlight_moa %in% names(moa_targets))] <- "other"

cp_umap_gg <- (
    ggplot(data = NULL, aes(x = UMAP_0, y = UMAP_1, color = highlight_moa, size = highlight_moa, alpha = highlight_moa))
    + geom_point(data = cp_df %>% dplyr::filter(highlight_moa == "other"))
    + geom_point(data = cp_df %>% dplyr::filter(dmso_label == "DMSO"), size = 2, color = "red", alpha = 0.1, aes(shape = dmso_label))
    + geom_point(data = cp_df %>% dplyr::filter(highlight_moa != "other"))
    + ggtitle("Cell Painting UMAP")
    + figure_theme
    + scale_size_manual("MOA", labels = moa_targets, values = moa_targets_size_values)
    + scale_alpha_manual("MOA", values = moa_targets_alpha_values)
    + scale_color_manual("MOA", labels = moa_targets, values = moa_colors)
    + scale_shape_manual("Control", values = c("DMSO" = 3))
    + xlab("UMAP X")
    + ylab("UMAP Y")
    + guides(alpha = FALSE, shape = guide_legend(override.aes = list(alpha = 0.8)))
)

cp_umap_gg

l1000_umap_gg <- (
     ggplot(data = NULL, aes(x = UMAP_0, y = UMAP_1, color = highlight_moa, size = highlight_moa, alpha = highlight_moa))
    + geom_point(data = l1000_df %>% dplyr::filter(highlight_moa == "other"))
    + geom_point(data = l1000_df %>% dplyr::filter(dmso_label == "DMSO"), size = 2, color = "red", alpha = 0.1, aes(shape = dmso_label))
    + geom_point(data = l1000_df %>% dplyr::filter(highlight_moa != "other"))
    + ggtitle("L1000 UMAP")
    + figure_theme
    + scale_size_manual("MOA", labels = moa_targets, values = moa_targets_size_values)
    + scale_alpha_manual("MOA", values = moa_targets_alpha_values)
    + scale_color_manual("MOA", labels = moa_targets, values = moa_colors)
    + scale_shape_manual("Control", values = c("DMSO" = 3))
    + xlab("UMAP X")
    + ylab("UMAP Y")
    + guides(alpha = FALSE, shape = guide_legend(override.aes = list(alpha = 0.8)))
)

l1000_umap_gg

# Load silhouette scores
silhouette_dir <- file.path("..", "3.clustering-pca", "results")

l1000_sil_file <- file.path(silhouette_dir, "L1000", "L1000_silhouette_scores_compounds_pass_threshold.csv")
cp_sil_file <- file.path(silhouette_dir, "cell_painting", "cp_silhouette_scores_compounds_pass_threshold.csv")

sil_cols <- readr::cols(
  cluster = readr::col_double(),
  Average_silhouette_score = readr::col_double(),
  dose = readr::col_character()
)

l1000_sil_df <- readr::read_csv(l1000_sil_file, col_types = sil_cols) %>% dplyr::mutate(assay = "L1000")
cp_sil_df <- readr::read_csv(cp_sil_file, col_types = sil_cols)  %>% dplyr::mutate(assay = "Cell Painting")

# Combine data
sil_df <- dplyr::bind_rows(l1000_sil_df, cp_sil_df) %>%
    dplyr::rename("metric_value" = "Average_silhouette_score") %>%
    dplyr::mutate("metric" = "Avg. silhouette width")

# Load Davies Bouldin scores
l1000_db_file <- file.path(silhouette_dir, "L1000", "L1000_davies_compounds_pass_threshold.csv")
cp_db_file <- file.path(silhouette_dir, "cell_painting", "cp_davies_compounds_pass_threshold.csv")

db_cols <- readr::cols(
  cluster = readr::col_double(),
  davies_bouldin_score = readr::col_double(),
  dose = readr::col_character()
)

l1000_db_df <- readr::read_csv(l1000_db_file, col_types = db_cols) %>% dplyr::mutate(assay = "L1000")
cp_db_df <- readr::read_csv(cp_db_file, col_types = db_cols)  %>% dplyr::mutate(assay = "Cell Painting")

# Combine data
db_df <- dplyr::bind_rows(l1000_db_df, cp_db_df) %>%
    dplyr::rename("metric_value" = "davies_bouldin_score") %>%
    dplyr::mutate("metric" = "Avg. Davies Bouldin score")

metric_df <- dplyr::bind_rows(db_df, sil_df)

metric_df$metric <- factor(metric_df$metric, levels = c("Avg. silhouette width", "Avg. Davies Bouldin score"))

head(metric_df)

panel_b_gg <- (
    ggplot(metric_df, aes(x = cluster, y = metric_value, color = assay, group = assay))
    + geom_point()
    + geom_line()
    + facet_wrap("~metric", scales = "free_y")
    + scale_color_manual("Assay", values = assay_colors)
    + figure_theme
    + ylab("Metric")
    + xlab("Cluster (k)")
)

panel_b_gg

# Load level 5 consensus signatures
consensus_dir <- file.path("..", "1.Data-exploration", "Consensus")

cp_df <- load_consensus_signatures(assay = "cellpainting", data_dir = consensus_dir)
l1000_df <- load_consensus_signatures(assay = "l1000", data_dir = consensus_dir)

cp_subset_df <- cp_df %>%
    dplyr::filter((Metadata_dose_recode >= 6) | (pert_iname == "dmso"))

cp_corr_df <- cp_subset_df %>%
    dplyr::select(starts_with(c("Cells", "Cytoplasm", "Nuclei"))) %>%
    as.matrix() %>%
    t() %>%
    Hmisc::rcorr(type = "spearman")

cp_corr_df <- cp_corr_df$r

cp_subset_metadata_df <- cp_subset_df %>%
    dplyr::select(Metadata_dose_recode, pert_iname, moa) %>%
    dplyr::mutate(id_number = row_number()) %>%
    dplyr::mutate(dmso_label = "DMSO")

cp_subset_metadata_df$dmso_label[cp_subset_metadata_df$pert_iname != "dmso"] = "compound"

cp_subset_metadata_df <- cp_subset_metadata_df %>% dplyr::mutate(highlight_moa = tolower(moa))
cp_subset_metadata_df$highlight_moa[!(cp_subset_metadata_df$highlight_moa %in% c("proteasome inhibitor"))] <- "other"
cp_subset_metadata_df$highlight_moa[cp_subset_metadata_df$pert_iname == "dmso"] <- "DMSO"

dim(cp_corr_df)

cp_heat_gg <- grid::grid.grabExpr(
    draw(
        Heatmap(
            cp_corr_df,

            column_title = "Cell Painting consensus signatures (10 uM)",

            top_annotation = HeatmapAnnotation(
                Perturbation = cp_subset_metadata_df$highlight_moa,
                col = list(Perturbation = heatmap_pert_colors),
                annotation_legend_param = list(
                    Perturbation = list(
                        title_gp = gpar(fontsize = lgd_title_fontsize),
                        labels_gp = gpar(fontsize = lgd_label_fontsize),
                        title = ""
                    )
                )
            ),

            heatmap_legend_param = list(
                    title = "Spearman\ncorrelation",
                    color_bar = "continuous",
                    col_fun = legend_scale_cols,
                    title_gp = gpar(fontsize = lgd_title_fontsize),
                    title_position = "topleft",
                    labels_gp = gpar(fontsize = lgd_label_fontsize),
                    legend_height = unit(3, "cm")
            )
        ),
        merge_legend = TRUE
    )
)

l1000_subset_df <- l1000_df %>%
    dplyr::filter((dose >= 6) | (pert_iname == "dmso"))

l1000_corr_df <- l1000_subset_df %>%
    dplyr::select(ends_with("at")) %>%
    as.matrix() %>%
    t() %>%
    Hmisc::rcorr(type = "spearman")

l1000_corr_df <- l1000_corr_df$r

l1000_subset_metadata_df <- l1000_subset_df %>%
    dplyr::select(dose, pert_iname, moa) %>%
    dplyr::mutate(id_number = row_number()) %>%
    dplyr::mutate(dmso_label = "DMSO")

l1000_subset_metadata_df$dmso_label[l1000_subset_metadata_df$pert_iname != "dmso"] = "compound"

l1000_subset_metadata_df <- l1000_subset_metadata_df %>% dplyr::mutate(highlight_moa = tolower(moa))
l1000_subset_metadata_df$highlight_moa[!(l1000_subset_metadata_df$highlight_moa %in% c("proteasome inhibitor"))] <- "other"
l1000_subset_metadata_df$highlight_moa[l1000_subset_metadata_df$pert_iname == "dmso"] <- "DMSO"

dim(l1000_corr_df)

l1000_heat_gg <- grid::grid.grabExpr(
    draw(
        Heatmap(
            l1000_corr_df,
            
            column_title = "L1000 consensus signatures (10 uM)",
            
            top_annotation = HeatmapAnnotation(
                Perturbation = l1000_subset_metadata_df$highlight_moa,
                col = list(Perturbation = heatmap_pert_colors),
                annotation_legend_param = list(
                    Perturbation = list(
                        title_gp = gpar(fontsize = lgd_title_fontsize),
                        labels_gp = gpar(fontsize = lgd_label_fontsize),
                        title = ""
                    )
                )
            ),

            heatmap_legend_param = list(
                title = "Spearman\ncorrelation",
                color_bar = "continuous",
                col_fun = legend_scale_cols,
                title_gp = gpar(fontsize = lgd_title_fontsize),
                title_position = "topleft",
                labels_gp = gpar(fontsize = lgd_label_fontsize),
                legend_height = unit(3, "cm")
            )
        ),
        merge_legend = TRUE
    )
)

heatmap_panels <- cowplot::plot_grid(
    cp_heat_gg,
    l1000_heat_gg,
    ncol = 2,
    labels = c("c", "")
)

figure3_gg <- cowplot::plot_grid(
    cowplot::plot_grid(
        cowplot::plot_grid(
            cp_umap_gg,
            l1000_umap_gg,
            ncol = 2,
            labels = c("a", "")
        ),
        panel_b_gg,
        nrow = 2,
        labels = c("", "b"),
        rel_heights = c(1, 0.4)
    ),
    heatmap_panels,
    rel_heights = c(1, 0.8),
    ncol = 1,
    labels = c("", "", "c")
)

figure3_gg

for (extension in extensions) {
    output_file <- paste0(output_figure_base, extension)
    cowplot::save_plot(output_file, figure3_gg, base_width = 11, base_height = 11, dpi = 500)
}
