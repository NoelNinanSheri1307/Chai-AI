import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../navigation/app_routes.dart';
import '../../services/settings_service.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_card.dart';
import '../../widgets/section_header.dart';
import '../../widgets/segmented_control.dart';

class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _endpointController;

  @override
  void initState() {
    super.initState();
    _endpointController = TextEditingController(
      text: context.read<SettingsService>().endpoint,
    );
  }

  @override
  void dispose() {
    _endpointController.dispose();
    super.dispose();
  }

  Future<void> _saveEndpoint() async {
    final value = _endpointController.text.trim();
    if (value.isEmpty) return;
    final settings = context.read<SettingsService>();
    await settings.setEndpoint(value);
    if (mounted) context.showSnack('Backend endpoint updated');
  }

  void _showModelInfo() {
    final colors = context.colors;
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Model Information'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'ForensicNet v2.1',
              style: AppTypography.label(colors.textPrimary),
            ),
            const SizedBox(height: 2),
            Text(
              'Primary authenticity classifier',
              style: AppTypography.caption(colors.textTertiary),
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              'ELA Classifier v1.0',
              style: AppTypography.label(colors.textPrimary),
            ),
            const SizedBox(height: 2),
            Text(
              'Error-level analysis engine',
              style: AppTypography.caption(colors.textTertiary),
            ),
            const SizedBox(height: AppSpacing.md),
            Text(
              'Metadata Anomaly Engine',
              style: AppTypography.label(colors.textPrimary),
            ),
            const SizedBox(height: 2),
            Text(
              'EXIF / provenance validation',
              style: AppTypography.caption(colors.textTertiary),
            ),
            const SizedBox(height: AppSpacing.md),
            Divider(color: colors.border),
            const SizedBox(height: AppSpacing.sm),
            Text(
              'Scores are simulated by a mock repository until the analysis backend is available.',
              style: AppTypography.caption(colors.textTertiary),
            ),
          ],
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Close'),
          ),
        ],
      ),
    );
  }

  void _showPrivacy() {
    final colors = context.colors;
    showModalBottomSheet(
      context: context,
      showDragHandle: true,
      builder: (context) => Padding(
        padding: const EdgeInsets.all(AppSpacing.lg),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Privacy', style: AppTypography.title(colors.textPrimary)),
            const SizedBox(height: AppSpacing.md),
            Text(
              'Uploaded images are processed for analysis and are not shared with third parties. Analysis history is stored locally on your device. When the analysis backend is enabled, images will be transmitted to the configured endpoint only.',
              style: AppTypography.body(colors.textSecondary),
            ),
            const SizedBox(height: AppSpacing.lg),
            AppButton(
              label: 'Got it',
              onPressed: () => Navigator.pop(context),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final settings = context.watch<SettingsService>();

    return Scaffold(
      appBar: AppBar(title: const Text('Settings')),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          children: [
            SectionHeader(title: 'Appearance'),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              child: SegmentedControl<ThemeMode>(
                value: settings.themeMode,
                onChanged: settings.setThemeMode,
                options: const [
                  SegmentedOption(ThemeMode.system, 'System', icon: Icons.brightness_auto),
                  SegmentedOption(ThemeMode.light, 'Light', icon: Icons.light_mode_outlined),
                  SegmentedOption(ThemeMode.dark, 'Dark', icon: Icons.dark_mode_outlined),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            SectionHeader(title: 'Language'),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              child: ListTile(
                contentPadding: EdgeInsets.zero,
                leading: Icon(Icons.language, color: colors.accent),
                title: Text(
                  settings.language.label,
                  style: AppTypography.label(colors.textPrimary),
                ),
                subtitle: Text(
                  'More languages coming soon',
                  style: AppTypography.caption(colors.textTertiary),
                ),
                trailing: const Icon(Icons.chevron_right, size: 20),
                onTap: () => context.showSnack('More languages coming soon'),
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            SectionHeader(
              title: 'Backend',
              subtitle: 'Active backend analysis endpoint',
            ),

            const SizedBox(height: AppSpacing.md),
            AppCard(
              child: Column(
                children: [
                  TextField(
                    controller: _endpointController,
                    keyboardType: TextInputType.url,
                    decoration: const InputDecoration(
                      labelText: 'API endpoint',
                      hintText: 'https://api.example.com',
                    ),
                  ),
                  const SizedBox(height: AppSpacing.md),
                  AppButton(
                    label: 'Save Endpoint',
                    variant: AppButtonVariant.outline,
                    onPressed: _saveEndpoint,
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),

            SectionHeader(title: 'About'),
            const SizedBox(height: AppSpacing.md),
            AppCard(
              padding: EdgeInsets.zero,
              child: Column(
                children: [
                  ListTile(
                    leading: Icon(Icons.smart_toy_outlined, color: colors.accent),
                    title: Text(
                      'Model Information',
                      style: AppTypography.label(colors.textPrimary),
                    ),
                    trailing: const Icon(Icons.chevron_right, size: 20),
                    onTap: _showModelInfo,
                  ),
                  Divider(color: colors.border, indent: AppSpacing.md),
                  ListTile(
                    leading: Icon(Icons.privacy_tip_outlined, color: colors.accent),
                    title: Text(
                      'Privacy',
                      style: AppTypography.label(colors.textPrimary),
                    ),
                    trailing: const Icon(Icons.chevron_right, size: 20),
                    onTap: _showPrivacy,
                  ),
                  Divider(color: colors.border, indent: AppSpacing.md),
                  ListTile(
                    leading: Icon(Icons.info_outline, color: colors.accent),
                    title: Text(
                      'About Chai AI',
                      style: AppTypography.label(colors.textPrimary),
                    ),
                    trailing: const Icon(Icons.chevron_right, size: 20),
                    onTap: () => Navigator.of(context).pushNamed(AppRoutes.about),
                  ),
                ],
              ),
            ),
            const SizedBox(height: AppSpacing.xl),
          ],
        ),
      ),
    );
  }
}
