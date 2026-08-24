import 'dart:convert';
import 'dart:typed_data';

import 'package:http/http.dart' as http;
import 'package:http_parser/http_parser.dart';

import '../../models/analysis_result.dart';
import '../../models/api_parsers.dart';
import '../analysis_repository.dart';

/// Backend-backed [AnalysisRepository] that talks to the Chai AI HTTP API.
class ApiAnalysisRepository implements AnalysisRepository {
  final String Function() _getBaseUrl;
  final http.Client _client;

  ApiAnalysisRepository(Object baseUrlOrGetter, {http.Client? client})
      : _getBaseUrl = baseUrlOrGetter is String Function()
            ? baseUrlOrGetter
            : (() => baseUrlOrGetter.toString()),
        _client = client ?? http.Client();

  String get baseUrl => _getBaseUrl().replaceAll(RegExp(r'/+$'), '');


  @override
  Future<AnalysisResult> analyzeImage({
    String? imagePath,
    Uint8List? imageBytes,
    String? fileName,
  }) async {
    final bytes = imageBytes;
    if (bytes == null) {
      throw ArgumentError('imageBytes is required to analyze via the API.');
    }
    final mime = sniffImageType(bytes);
    final request =
        http.MultipartRequest('POST', Uri.parse('$baseUrl/v1/analyses'))
          ..files.add(http.MultipartFile.fromBytes(
            'file',
            bytes,
            filename: fileName ?? 'image',
            contentType: MediaType.parse(mime),
          ));

    final json = await _sendMultipart(request);
    final result = parseAnalysisResult(json);
    return result.copyWith(
      imageBytes: bytes,
      fileName: fileName ?? result.fileName,
    );
  }


  Future<Map<String, dynamic>> _sendMultipart(
    http.MultipartRequest request,
  ) async {
    final streamed = await _client.send(request).timeout(
      const Duration(seconds: 120),
      onTimeout: () => throw http.ClientException(
        'Request timed out. The server took longer than 120 seconds.',
        request.url,
      ),
    );


    final response = await http.Response.fromStream(streamed);
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return jsonDecode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
    }
    final msg = _errorMessage(response) ?? 'Backend returned ${response.statusCode}.';
    throw http.ClientException(msg, response.request?.url);
  }


  String? _errorMessage(http.Response response) {
    try {
      final body = jsonDecode(utf8.decode(response.bodyBytes));
      final error = (body as Map<String, dynamic>)['error'];
      if (error is Map<String, dynamic> && error['message'] is String) {
        return error['message'] as String;
      }
    } catch (_) {
      // Fall through to the generic message.
    }
    return null;
  }
}

/// Determine the image MIME type from magic bytes (mirrors the backend sniffer).
String sniffImageType(Uint8List? bytes) {
  final data = bytes;
  if (data != null && data.length >= 4) {
    if (data[0] == 0xFF && data[1] == 0xD8 && data[2] == 0xFF) {
      return 'image/jpeg';
    }
    if (data[0] == 0x89 &&
        data[1] == 0x50 &&
        data[2] == 0x4E &&
        data[3] == 0x47) {
      return 'image/png';
    }
    if (data[0] == 0x52 &&
        data[1] == 0x49 &&
        data[2] == 0x46 &&
        data[3] == 0x46 &&
        data.length >= 12 &&
        String.fromCharCodes(data.sublist(8, 12)) == 'WEBP') {
      return 'image/webp';
    }
  }
  return 'image/jpeg';
}
