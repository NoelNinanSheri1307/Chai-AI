import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../../providers/history_provider.dart';
import '../../core/spacing.dart';
import '../../core/app_colors.dart';
import '../../core/app_text_styles.dart';
import '../../providers/auth_provider.dart';
import 'package:fl_chart/fl_chart.dart';

class DashboardHomeScreen extends StatelessWidget {
  const DashboardHomeScreen({super.key});

  @override
  Widget build(BuildContext context) {
    final authProvider = Provider.of<AuthProvider>(context);
    final historyProvider = Provider.of<HistoryProvider>(context);
    final history = historyProvider.history;

    int totalScans = history.length;
    int lowRisk = history.where((e) => e.riskLevel == "Low").length;
    int mediumRisk = history.where((e) => e.riskLevel == "Medium").length;
    int highRisk = history.where((e) => e.riskLevel == "High").length;

    final isDark = Theme.of(context).brightness == Brightness.dark;

    final primaryText = isDark
        ? AppColors.darkTextPrimary
        : AppColors.lightTextPrimary;
    final secondaryText = isDark
        ? AppColors.darkTextSecondary
        : AppColors.lightTextSecondary;
    final cardColor = isDark ? AppColors.darkCard : AppColors.lightCard;
    final borderColor = isDark ? AppColors.darkBorder : AppColors.lightBorder;

    return SingleChildScrollView(
      padding: const EdgeInsets.all(AppSpacing.lg),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            "Welcome, ${authProvider.user?.name}",
            style: AppTextStyles.headingLarge(primaryText),
          ),
          const SizedBox(height: AppSpacing.sm),
          Text(
            "Monitor image authenticity and risk insights",
            style: AppTextStyles.body(secondaryText),
          ),
          const SizedBox(height: AppSpacing.xl),

          if (totalScans == 0)
            Padding(
              padding: const EdgeInsets.only(top: AppSpacing.xl),
              child: Text(
                "No analyses yet. Run a scan to see insights.",
                style: AppTextStyles.body(secondaryText),
              ),
            )
          else
            _StatsGrid(
              totalScans: totalScans,
              lowRisk: lowRisk,
              mediumRisk: mediumRisk,
              highRisk: highRisk,
            ),

          const SizedBox(height: AppSpacing.xl),

          Text(
            "Risk Distribution",
            style: AppTextStyles.headingMedium(primaryText),
          ),
          const SizedBox(height: AppSpacing.md),

          Container(
            height: 200,
            padding: const EdgeInsets.all(AppSpacing.md),
            decoration: BoxDecoration(
              color: cardColor,
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: borderColor),
            ),
            child: PieChart(
              PieChartData(
                sections: [
                  PieChartSectionData(
                    value: lowRisk.toDouble(),
                    color: AppColors.riskLow,
                    title: "Low",
                  ),
                  PieChartSectionData(
                    value: mediumRisk.toDouble(),
                    color: AppColors.riskMedium,
                    title: "Medium",
                  ),
                  PieChartSectionData(
                    value: highRisk.toDouble(),
                    color: AppColors.riskHigh,
                    title: "High",
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: AppSpacing.xl + 4),

          // RECENT ANALYSES
          Text(
            "Recent Analyses",
            style: AppTextStyles.headingMedium(primaryText),
          ),

          const SizedBox(height: AppSpacing.md),

          if (history.where((e) => e.type == "analysis").isEmpty)
            Text("No recent analyses", style: AppTextStyles.body(secondaryText))
          else
            Column(
              children: history.where((e) => e.type == "analysis").take(3).map((
                item,
              ) {
                return Container(
                  margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: cardColor,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: borderColor),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("Score: ${item.authenticityScore.toInt()}%"),
                      Text(item.riskLevel),
                    ],
                  ),
                );
              }).toList(),
            ),

          const SizedBox(height: AppSpacing.xl),

          // RECENT SAFETY CHECKS
          Text(
            "Recent Safety Checks",
            style: AppTextStyles.headingMedium(primaryText),
          ),

          const SizedBox(height: AppSpacing.md),

          if (history.where((e) => e.type == "safety").isEmpty)
            Text(
              "No recent safety checks",
              style: AppTextStyles.body(secondaryText),
            )
          else
            Column(
              children: history.where((e) => e.type == "safety").take(3).map((
                item,
              ) {
                return Container(
                  margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: cardColor,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: borderColor),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("Score: ${item.authenticityScore.toInt()}%"),
                      Text(item.riskLevel),
                    ],
                  ),
                );
              }).toList(),
            ),

          const SizedBox(height: AppSpacing.md),

          if (history.isEmpty)
            Text("No recent activity", style: AppTextStyles.body(secondaryText))
          else
            Column(
              children: history.take(3).map((item) {
                return Container(
                  margin: const EdgeInsets.only(bottom: AppSpacing.sm),
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: cardColor,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: borderColor),
                  ),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text("Score: ${item.authenticityScore.toInt()}%"),
                      Text(item.riskLevel),
                    ],
                  ),
                );
              }).toList(),
            ),

          const SizedBox(height: AppSpacing.xl),

          Text(
            "Why AI Safety Checks Matter",
            style: AppTextStyles.headingMedium(primaryText),
          ),

          const SizedBox(height: AppSpacing.md),

          _buildSafetyStats(cardColor, borderColor, primaryText, secondaryText),
          const SizedBox(height: AppSpacing.xl),

          Text(
            "AI Threat Growth Trend",
            style: AppTextStyles.headingMedium(primaryText),
          ),

          const SizedBox(height: AppSpacing.md),

          _buildThreatTrendChart(cardColor, borderColor),
        ],
      ),
    );
  }
}

Widget _buildSafetyStats(
  Color cardColor,
  Color borderColor,
  Color primaryText,
  Color secondaryText,
) {
  return Column(
    children: [
      _safetyStatCard(
        cardColor,
        borderColor,
        primaryText,
        secondaryText,
        "Deepfake usage increased by 900% in recent years.",
      ),
      const SizedBox(height: AppSpacing.sm),
      _safetyStatCard(
        cardColor,
        borderColor,
        primaryText,
        secondaryText,
        "AI-generated phishing images are bypassing manual moderation.",
      ),
      const SizedBox(height: AppSpacing.sm),
      _safetyStatCard(
        cardColor,
        borderColor,
        primaryText,
        secondaryText,
        "Automated authenticity checks reduce moderation load significantly.",
      ),
    ],
  );
}

Widget _buildThreatTrendChart(Color cardColor, Color borderColor) {
  return Container(
    height: 260,
    padding: const EdgeInsets.all(AppSpacing.md),
    decoration: BoxDecoration(
      color: cardColor,
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: borderColor),
    ),
    child: LineChart(
      LineChartData(
        minY: 0,
        maxY: 130,
        gridData: FlGridData(show: true, horizontalInterval: 20),
        borderData: FlBorderData(show: true),
        titlesData: FlTitlesData(
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              interval: 20,
              getTitlesWidget: (value, meta) {
                return Text(
                  value.toInt().toString(),
                  style: const TextStyle(fontSize: 10),
                );
              },
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              getTitlesWidget: (value, meta) {
                switch (value.toInt()) {
                  case 0:
                    return const Text("2019", style: TextStyle(fontSize: 10));
                  case 1:
                    return const Text("2020", style: TextStyle(fontSize: 10));
                  case 2:
                    return const Text("2021", style: TextStyle(fontSize: 10));
                  case 3:
                    return const Text("2022", style: TextStyle(fontSize: 10));
                  case 4:
                    return const Text("2023", style: TextStyle(fontSize: 10));
                  case 5:
                    return const Text("2024", style: TextStyle(fontSize: 10));
                }
                return const SizedBox();
              },
            ),
          ),
          rightTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
          topTitles: const AxisTitles(
            sideTitles: SideTitles(showTitles: false),
          ),
        ),
        lineBarsData: [
          LineChartBarData(
            isCurved: true,
            color: AppColors.riskHigh,
            barWidth: 3,
            dotData: FlDotData(
              show: true,
              getDotPainter: (spot, percent, barData, index) {
                return FlDotCirclePainter(
                  radius: 4,
                  color: AppColors.riskHigh,
                  strokeWidth: 2,
                  strokeColor: Colors.white,
                );
              },
            ),

            spots: const [
              FlSpot(0, 10),
              FlSpot(1, 25),
              FlSpot(2, 40),
              FlSpot(3, 60),
              FlSpot(4, 85),
              FlSpot(5, 120),
            ],
          ),
        ],
      ),
    ),
  );
}

Widget _safetyStatCard(
  Color cardColor,
  Color borderColor,
  Color primaryText,
  Color secondaryText,
  String text,
) {
  return Container(
    decoration: BoxDecoration(
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: borderColor),
    ),
    child: Row(
      children: [
        Container(
          width: 4,
          decoration: BoxDecoration(
            color: secondaryText.withOpacity(0.4),
            borderRadius: const BorderRadius.only(
              topLeft: Radius.circular(8),
              bottomLeft: Radius.circular(8),
            ),
          ),
        ),
        Expanded(
          child: Container(
            padding: const EdgeInsets.all(AppSpacing.md),
            color: cardColor,
            child: Row(
              children: [
                Icon(Icons.info_outline, color: secondaryText),
                const SizedBox(width: AppSpacing.md),
                Expanded(
                  child: Text(text, style: AppTextStyles.body(secondaryText)),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}

class _StatsGrid extends StatelessWidget {
  final int totalScans;
  final int lowRisk;
  final int mediumRisk;
  final int highRisk;

  const _StatsGrid({
    required this.totalScans,
    required this.lowRisk,
    required this.mediumRisk,
    required this.highRisk,
  });

  @override
  Widget build(BuildContext context) {
    return GridView.count(
      crossAxisCount: 2,
      crossAxisSpacing: AppSpacing.md,
      mainAxisSpacing: AppSpacing.md,
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      children: [
        _StatCard("Total Scans", totalScans.toString(), null),
        _StatCard("Low Risk", lowRisk.toString(), AppColors.riskLow),
        _StatCard("Medium Risk", mediumRisk.toString(), AppColors.riskMedium),
        _StatCard("High Risk", highRisk.toString(), AppColors.riskHigh),
      ],
    );
  }
}

class _StatCard extends StatefulWidget {
  final String title;
  final String value;
  final Color? accentColor;

  const _StatCard(this.title, this.value, this.accentColor, {super.key});
  @override
  State<_StatCard> createState() => _StatCardState();
}

class _StatCardState extends State<_StatCard>
    with SingleTickerProviderStateMixin {
  AnimationController? _controller;
  Animation<double>? _animation;

  @override
  void initState() {
    super.initState();

    final target = double.tryParse(widget.value) ?? 0;

    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 800),
    );

    _animation = Tween<double>(
      begin: 0,
      end: target,
    ).animate(CurvedAnimation(parent: _controller!, curve: Curves.easeOut));

    _controller!.forward();
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  void didUpdateWidget(covariant _StatCard oldWidget) {
    super.didUpdateWidget(oldWidget);

    if (oldWidget.value != widget.value) {
      final target = double.tryParse(widget.value) ?? 0;
      _animation = Tween<double>(
        begin: 0,
        end: target,
      ).animate(CurvedAnimation(parent: _controller!, curve: Curves.easeOut));
      _controller!.forward(from: 0);
    }
  }

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

    return Container(
      constraints: const BoxConstraints(minHeight: 100),
      decoration: BoxDecoration(
        color: cardColor,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: borderColor),
      ),
      child: Row(
        children: [
          if (widget.accentColor != null)
            Container(
              width: 6,
              decoration: BoxDecoration(
                color: widget.accentColor,
                borderRadius: const BorderRadius.only(
                  topLeft: Radius.circular(8),
                  bottomLeft: Radius.circular(8),
                ),
              ),
            ),

          Expanded(
            child: Padding(
              padding: const EdgeInsets.all(AppSpacing.md),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  Text(widget.title, style: AppTextStyles.body(secondaryText)),
                  const SizedBox(height: AppSpacing.sm),
                  if (_animation == null)
                    Text(
                      widget.value,
                      style: AppTextStyles.headingMedium(primaryText),
                    )
                  else
                    AnimatedBuilder(
                      animation: _animation!,
                      builder: (context, child) {
                        return Text(
                          _animation!.value.toInt().toString(),
                          style: AppTextStyles.headingMedium(primaryText),
                        );
                      },
                    ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}
