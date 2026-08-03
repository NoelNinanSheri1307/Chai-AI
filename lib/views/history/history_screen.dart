import 'dart:io';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../models/analysis_result_model.dart';
import '../../providers/history_provider.dart';
import '../../core/spacing.dart';
import '../../core/app_colors.dart';
import '../../core/app_text_styles.dart';
import '../result/result_screen.dart';

class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final historyProvider = Provider.of<HistoryProvider>(context);
    final history = historyProvider.history;
    final isDark = Theme.of(context).brightness == Brightness.dark;

    final cardColor = isDark ? AppColors.darkCard : AppColors.lightCard;
    final borderColor = isDark ? AppColors.darkBorder : AppColors.lightBorder;
    final primaryText = isDark
        ? AppColors.darkTextPrimary
        : AppColors.lightTextPrimary;

    if (history.isEmpty) {
      return const Center(child: Text("No analysis history yet"));
    }

    return ListView.builder(
      padding: const EdgeInsets.all(AppSpacing.lg),
      itemCount: history.length,
      itemBuilder: (context, index) {
        final item = history[index];

        return Dismissible(
          key: Key(item.id),
          direction: DismissDirection.endToStart,
          background: Container(
            alignment: Alignment.centerRight,
            padding: const EdgeInsets.symmetric(horizontal: AppSpacing.lg),
            decoration: BoxDecoration(
              color: Colors.red,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Icon(Icons.delete, color: Colors.white),
          ),
          confirmDismiss: (_) async {
            return await showDialog(
              context: context,
              builder: (context) => AlertDialog(
                title: const Text("Delete Entry"),
                content: const Text(
                  "Are you sure you want to delete this analysis record?",
                ),
                actions: [
                  TextButton(
                    onPressed: () => Navigator.pop(context, false),
                    child: const Text("Cancel"),
                  ),
                  TextButton(
                    onPressed: () => Navigator.pop(context, true),
                    child: const Text(
                      "Delete",
                      style: TextStyle(color: Colors.red),
                    ),
                  ),
                ],
              ),
            );
          },
          onDismissed: (_) {
            Provider.of<HistoryProvider>(
              context,
              listen: false,
            ).removeHistoryItem(item.id);
          },
          child: Container(
            margin: const EdgeInsets.only(bottom: AppSpacing.md),
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: cardColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: borderColor),
            ),
            child: ListTile(
              leading: item.imagePath != null
                  ? Image.file(
                      File(item.imagePath!),
                      width: 50,
                      fit: BoxFit.cover,
                    )
                  : null,
              title: Text(
                "Score: ${item.authenticityScore.toInt()}%",
                style: AppTextStyles.body(primaryText),
              ),
              subtitle: Text(item.riskLevel),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text("${item.timestamp.hour}:${item.timestamp.minute}"),
                  const SizedBox(width: AppSpacing.sm),
                ],
              ),

              onTap: () {
                Navigator.push(
                  context,
                  MaterialPageRoute(
                    builder: (_) => ResultScreen(
                      result: AnalysisResult(
                        authenticityScore: item.authenticityScore,
                        riskLevel: item.riskLevel,
                        enforcementAction: item.riskLevel == "Low"
                            ? "Allow"
                            : item.riskLevel == "Medium"
                            ? "Review"
                            : "Block",
                        aiScore: 0.0,
                        manipulationScore: 0.0,
                        frequencyScore: 0.0,
                        metadataFlag: false,
                        explanation: "Loaded from history",
                      ),
                      imagePath: item.imagePath,
                      saveToHistory: false,
                    ),
                  ),
                );
              },
            ),
          ),
        );
      },
    );
  }
}
