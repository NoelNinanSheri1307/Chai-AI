// lib/views/safety/file_safety_screen.dart

import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../../core/app_colors.dart';
import '../../core/app_text_styles.dart';
import '../../core/spacing.dart';
import '../../models/analysis_result_model.dart';
import '../../services/analysis_screen.dart';
import 'package:provider/provider.dart';
import '../../providers/history_provider.dart';
import '../../models/history_item_model.dart';
import '../../services/report_service.dart';
import 'package:share_plus/share_plus.dart';
import '../analysis/processing_screen.dart';

class FileSafetyScreen extends StatefulWidget {
  const FileSafetyScreen({super.key});

  @override
  State<FileSafetyScreen> createState() => _FileSafetyScreenState();
}

class _FileSafetyScreenState extends State<FileSafetyScreen> {
  File? selectedImage;
  AnalysisResult? result;
  bool isAnalyzing = false;
  final ImagePicker _picker = ImagePicker();
  bool _showResultAnimation = false;
  bool _isBlockedPulse = false;

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final cardColor = isDark ? AppColors.darkCard : AppColors.lightCard;
    final borderColor = isDark ? AppColors.darkBorder : AppColors.lightBorder;
    final primaryText = isDark
        ? AppColors.darkTextPrimary
        : AppColors.lightTextPrimary;
    final secondaryText = isDark
        ? AppColors.darkTextSecondary
        : AppColors.lightTextSecondary;

    return Scaffold(
      appBar: AppBar(title: const Text("File Safety Check")),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _buildUploadSection(cardColor, borderColor, primaryText),
            const SizedBox(height: AppSpacing.xl),

            if (isAnalyzing) const Center(child: CircularProgressIndicator()),

            if (result != null)
              _buildEnforcementSection(
                result!,
                cardColor,
                borderColor,
                primaryText,
                secondaryText,
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildUploadSection(
    Color cardColor,
    Color borderColor,
    Color primaryText,
  ) {
    return Container(
      padding: const EdgeInsets.all(AppSpacing.lg),
      decoration: BoxDecoration(
        color: cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: borderColor),
      ),
      child: Column(
        children: [
          Text(
            "Upload Image For Safety Check",
            style: AppTextStyles.headingMedium(primaryText),
          ),
          const SizedBox(height: AppSpacing.md),

          ElevatedButton(
            onPressed: () async {
              final XFile? picked = await _picker.pickImage(
                source: ImageSource.gallery,
              );

              if (picked != null) {
                setState(() {
                  selectedImage = File(picked.path);
                  result = null;
                });
              }
            },
            child: const Text("Select Image"),
          ),

          if (selectedImage != null) ...[
            const SizedBox(height: AppSpacing.md),
            Image.file(selectedImage!, height: 200, fit: BoxFit.cover),
            const SizedBox(height: AppSpacing.md),
            ElevatedButton(
              onPressed: () {
                if (selectedImage == null) return;

                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) =>
                        ProcessingScreen(imagePath: selectedImage!.path),
                  ),
                );
              },
              child: const Text("Analyze Safety"),
            ),
          ],
        ],
      ),
    );
  }

  Future<void> _runRealAnalysis() async {
    if (selectedImage == null) return;

    setState(() {
      isAnalyzing = true;
      result = null;
    });

    try {
      final analysis = await AnalysisService.analyzeImage(selectedImage!);
      final historyProvider = Provider.of<HistoryProvider>(
        context,
        listen: false,
      );

      historyProvider.addHistoryItem(
        HistoryItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          imagePath: selectedImage?.path,
          authenticityScore: analysis.authenticityScore,
          riskLevel: analysis.riskLevel,
          timestamp: DateTime.now(),
          type: "safety",
        ),
      );

      setState(() {
        result = analysis;
        isAnalyzing = false;
        _isBlockedPulse = analysis.enforcementAction == "Block";
      });
    } catch (e) {
      setState(() {
        isAnalyzing = false;
      });

      ScaffoldMessenger.of(
        context,
      ).showSnackBar(const SnackBar(content: Text("Analysis failed")));
    }
  }

  Widget _buildEnforcementSection(
    AnalysisResult result,
    Color cardColor,
    Color borderColor,
    Color primaryText,
    Color secondaryText,
  ) {
    Color bannerColor;
    IconData icon;
    String title;

    switch (result.enforcementAction) {
      case "Allow":
        bannerColor = AppColors.riskLow;
        icon = Icons.check_circle;
        title = "Upload Approved";
        break;
      case "Review":
        bannerColor = AppColors.riskMedium;
        icon = Icons.warning;
        title = "Under Review Required";
        break;
      default:
        bannerColor = AppColors.riskHigh;
        icon = Icons.block;
        title = "Upload Blocked";
    }

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          padding: const EdgeInsets.all(AppSpacing.lg),
          decoration: BoxDecoration(
            color: bannerColor.withOpacity(0.15),
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: bannerColor),
          ),
          child: Row(
            children: [
              Icon(icon, color: bannerColor, size: 48),
              const SizedBox(width: AppSpacing.md),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      title,
                      style: AppTextStyles.headingMedium(primaryText),
                    ),
                    const SizedBox(height: AppSpacing.sm),
                    Text(
                      result.explanation,
                      style: AppTextStyles.body(secondaryText),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),

        const SizedBox(height: AppSpacing.xl),

        Text(
          "Authenticity Score: ${result.authenticityScore.toStringAsFixed(4)}%",
        ),
        Text("AI Score: ${(result.aiScore * 100).toInt()}%"),
        Text(
          "Manipulation Score: ${(result.manipulationScore * 100).toInt()}%",
        ),

        const SizedBox(height: AppSpacing.xl),

        Row(
          children: [
            ElevatedButton(
              onPressed: () => ReportService.generateReport(result),
              child: const Text("Export PDF"),
            ),
            const SizedBox(width: AppSpacing.md),
            ElevatedButton(
              onPressed: () {
                Share.share(
                  "Authenticity Score: ${result.authenticityScore}%\n"
                  "Risk Level: ${result.riskLevel}\n"
                  "Action: ${result.enforcementAction}",
                );
              },
              child: const Text("Share"),
            ),
          ],
        ),
      ],
    );
  }
}
