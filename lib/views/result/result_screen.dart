import 'package:flutter/material.dart';
import 'dart:io';
import '../../core/app_colors.dart';
import '../../core/app_text_styles.dart';
import '../../core/spacing.dart';
import '../../models/analysis_result_model.dart';
import 'package:percent_indicator/circular_percent_indicator.dart';
import 'package:provider/provider.dart';
import '../../providers/history_provider.dart';
import '../../models/history_item_model.dart';
import '../dashboard/main_dashboard.dart';
import '../../services/report_service.dart';

class ResultScreen extends StatefulWidget {
  final AnalysisResult result;
  final String? imagePath;
  final bool saveToHistory;

  const ResultScreen({
    super.key,
    required this.result,
    this.imagePath,
    this.saveToHistory = true,
  });

  @override
  State<ResultScreen> createState() => _ResultScreenState();
}

class _ResultScreenState extends State<ResultScreen> {
  @override
  void initState() {
    super.initState();

    if (!widget.saveToHistory) return;

    Future.microtask(() {
      final historyProvider = Provider.of<HistoryProvider>(
        context,
        listen: false,
      );

      historyProvider.addHistoryItem(
        HistoryItem(
          id: DateTime.now().millisecondsSinceEpoch.toString(),
          imagePath: widget.imagePath,
          authenticityScore: widget.result.authenticityScore,
          riskLevel: widget.result.riskLevel,
          timestamp: DateTime.now(),
          type: "analysis",
        ),
      );
    });
  }

  Color _getRiskColor(String risk) {
    switch (risk) {
      case "Low":
        return AppColors.riskLow;
      case "High":
        return AppColors.riskHigh;
      default:
        return AppColors.riskMedium;
    }
  }

  @override
  Widget build(BuildContext context) {
    final result = widget.result;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final primaryText = isDark
        ? AppColors.darkTextPrimary
        : AppColors.lightTextPrimary;
    final secondaryText = isDark
        ? AppColors.darkTextSecondary
        : AppColors.lightTextSecondary;
    final cardColor = isDark ? AppColors.darkCard : AppColors.lightCard;
    final borderColor = isDark ? AppColors.darkBorder : AppColors.lightBorder;

    final riskColor = _getRiskColor(result.riskLevel);

    return Scaffold(
      appBar: AppBar(
        title: const Text("Analysis Result"),
        actions: [
          IconButton(
            icon: const Icon(Icons.picture_as_pdf),
            onPressed: () {
              ReportService.generateReport(result);
            },
          ),
          IconButton(
            icon: const Icon(Icons.home),
            onPressed: () {
              Navigator.of(context).pushAndRemoveUntil(
                MaterialPageRoute(builder: (_) => const MainDashboard()),
                (route) => false,
              );
            },
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          children: [
            if (widget.imagePath != null)
              Image.file(File(widget.imagePath!), height: 250),

            const SizedBox(height: 20),

            CircularPercentIndicator(
              radius: 90,
              lineWidth: 10,
              percent: result.authenticityScore / 100,
              circularStrokeCap: CircularStrokeCap.round,
              progressColor: riskColor,
              backgroundColor: borderColor,
              center: Text(
                "${result.authenticityScore.toInt()}%",
                style: AppTextStyles.scoreLarge(primaryText),
              ),
            ),

            const SizedBox(height: 20),

            Text(
              result.riskLevel,
              style: TextStyle(
                color: riskColor,
                fontSize: 18,
                fontWeight: FontWeight.bold,
              ),
            ),

            const SizedBox(height: 20),

            Text(result.explanation, style: AppTextStyles.body(secondaryText)),
          ],
        ),
      ),
    );
  }
}
