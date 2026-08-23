import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';

import '../../core/theme/app_dimensions.dart';
import '../../core/theme/app_typography.dart';
import '../../core/utils/context_ext.dart';
import '../../navigation/app_routes.dart';
import '../../services/quota_service.dart';
import '../../widgets/app_button.dart';
import '../../widgets/app_card.dart';
import '../../widgets/drop_zone.dart';
import '../../widgets/image_thumb.dart';

class UploadScreen extends StatefulWidget {
  const UploadScreen({super.key});

  @override
  State<UploadScreen> createState() => _UploadScreenState();
}

class _UploadScreenState extends State<UploadScreen> {
  final ImagePicker _picker = ImagePicker();

  String? _name;
  Uint8List? _bytes;
  bool _loading = false;

  bool get _isDesktopOrWeb =>
      kIsWeb ||
      defaultTargetPlatform == TargetPlatform.windows ||
      defaultTargetPlatform == TargetPlatform.linux ||
      defaultTargetPlatform == TargetPlatform.macOS;

  Future<void> _pick(ImageSource source) async {
    if (_loading) return;
    try {
      final picked = await _picker.pickImage(source: source);
      if (picked == null) return;
      final bytes = await picked.readAsBytes();
      if (!mounted) return;
      setState(() {
        _name = picked.name.isNotEmpty ? picked.name : 'image';
        _bytes = bytes;
      });
    } catch (_) {
      if (mounted) context.showSnack('Could not load the selected image.');
    }
  }

  Future<void> _startAnalysis() async {
    if (_bytes == null || _loading) return;
    final quota = context.read<QuotaService>();
    if (!quota.hasRemainingQuota) {
      _showQuotaExceededDialog();
      return;
    }
    final allowed = await quota.consumeScan();
    if (!allowed) {
      if (mounted) _showQuotaExceededDialog();
      return;
    }

    setState(() => _loading = true);
    await Future<void>.delayed(const Duration(milliseconds: 120));
    if (!mounted) return;
    Navigator.of(context).pushReplacementNamed(
      AppRoutes.processing,
      arguments: ProcessingArgs(_name ?? 'image', _bytes),
    );
  }

  void _showQuotaExceededDialog() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Row(
          children: [
            Icon(Icons.bolt, color: Colors.amber),
            SizedBox(width: 8),
            Text('Daily Limit Reached'),
          ],
        ),
        content: const Text(
          'You have reached your daily quota of 10 free scans.\n\nYour scan limit will reset automatically tomorrow.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context),
            child: const Text('Got it'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    final quota = context.watch<QuotaService>();
    final hasImage = _bytes != null;
    final canAnalyze = hasImage && quota.hasRemainingQuota;

    return Scaffold(
      appBar: AppBar(title: const Text('New Analysis')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(AppSpacing.lg),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Text(
                      'Upload an image',
                      style: AppTypography.headline(colors.textPrimary),
                    ),
                  ),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: (quota.hasRemainingQuota ? colors.accent : colors.warning)
                          .withValues(alpha: 0.12),
                      borderRadius: BorderRadius.circular(AppRadius.pill),
                    ),
                    child: Text(
                      '${quota.remainingUploads}/${quota.maxUploads} left today',
                      style: AppTypography.caption(
                        quota.hasRemainingQuota ? colors.accent : colors.warning,
                      ).copyWith(fontWeight: FontWeight.bold),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: AppSpacing.sm),
              Text(
                'We run a forensic pipeline and explain every verdict.',
                style: AppTypography.body(colors.textSecondary),
              ),
              if (!quota.hasRemainingQuota) ...[
                const SizedBox(height: AppSpacing.md),
                Container(
                  padding: const EdgeInsets.all(AppSpacing.md),
                  decoration: BoxDecoration(
                    color: colors.warning.withValues(alpha: 0.12),
                    borderRadius: BorderRadius.circular(AppRadius.md),
                    border: Border.all(color: colors.warning.withValues(alpha: 0.3)),
                  ),
                  child: Row(
                    children: [
                      Icon(Icons.info_outline, color: colors.warning, size: 20),
                      const SizedBox(width: AppSpacing.sm),
                      Expanded(
                        child: Text(
                          'Daily limit reached (10/10 scans). Quota resets tomorrow.',
                          style: AppTypography.caption(colors.warning),
                        ),
                      ),
                    ],
                  ),
                ),
              ],
              const SizedBox(height: AppSpacing.xl),


              if (_isDesktopOrWeb)
                DragDropZone(
                  onFiles: (files) async {
                    final file = files.first;
                    final bytes = await file.readAsBytes();
                    if (!mounted) return;
                    setState(() {
                      _name = file.name.isNotEmpty ? file.name : 'image';
                      _bytes = bytes;
                    });
                  },
                  onTap: () => _pick(ImageSource.gallery),
                  child: AppCard(
                    padding: const EdgeInsets.symmetric(vertical: AppSpacing.xl),
                    child: hasImage
                        ? _SelectedPreview(name: _name, bytes: _bytes)
                        : const DropHint(
                            icon: Icons.file_upload_outlined,
                            title: 'Drop an image here',
                            subtitle:
                                'PNG, JPEG or WebP. Drag & drop to analyze.',
                          ),
                  ),
                )
              else
                AppCard(
                  padding: const EdgeInsets.symmetric(vertical: AppSpacing.xl),
                  child: hasImage
                      ? _SelectedPreview(name: _name, bytes: _bytes)
                      : const DropHint(
                          icon: Icons.image_outlined,
                          title: 'Choose an image',
                          subtitle: 'Pick from your gallery or take a photo.',
                        ),
                ),

              if (hasImage) ...[
                const SizedBox(height: AppSpacing.md),
                Row(
                  children: [
                    Expanded(
                      child: AppButton(
                        label: 'Replace',
                        variant: AppButtonVariant.outline,
                        icon: Icons.refresh,
                        onPressed: () => setState(() {
                          _name = null;
                          _bytes = null;
                        }),
                      ),
                    ),
                    if (_isDesktopOrWeb) ...[
                      const SizedBox(width: AppSpacing.md),
                      Expanded(
                        child: AppButton(
                          label: 'Browse',
                          variant: AppButtonVariant.outline,
                          icon: Icons.folder_open,
                          onPressed: () => _pick(ImageSource.gallery),
                        ),
                      ),
                    ],
                  ],
                ),
              ] else if (!_isDesktopOrWeb) ...[
                const SizedBox(height: AppSpacing.lg),
                AppButton(
                  label: 'Select from Gallery',
                  icon: Icons.photo_library_outlined,
                  onPressed: () => _pick(ImageSource.gallery),
                ),
                const SizedBox(height: AppSpacing.sm),
                if (defaultTargetPlatform == TargetPlatform.android ||
                    defaultTargetPlatform == TargetPlatform.iOS)
                  AppButton(
                    label: 'Capture from Camera',
                    variant: AppButtonVariant.outline,
                    icon: Icons.photo_camera_outlined,
                    onPressed: () => _pick(ImageSource.camera),
                  ),
              ],

              const SizedBox(height: AppSpacing.xl),
              AppButton(
                label: 'Analyze Image',
                icon: Icons.auto_awesome,
                loading: _loading,
                onPressed: canAnalyze ? _startAnalysis : null,
              ),

            ],
          ),
        ),
      ),
    );
  }
}

class _SelectedPreview extends StatelessWidget {
  final String? name;
  final Uint8List? bytes;

  const _SelectedPreview({this.name, this.bytes});

  @override
  Widget build(BuildContext context) {
    final colors = context.colors;
    return Column(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(AppRadius.lg),
          child: SizedBox(
            height: 240,
            width: double.infinity,
            child: bytes != null
                ? Image.memory(bytes!, fit: BoxFit.cover)
                : ImageThumb(size: 120),
          ),
        ),
        const SizedBox(height: AppSpacing.md),
        Text(
          name ?? 'Image',
          maxLines: 1,
          overflow: TextOverflow.ellipsis,
          style: AppTypography.label(colors.textPrimary),
        ),
      ],
    );
  }
}
