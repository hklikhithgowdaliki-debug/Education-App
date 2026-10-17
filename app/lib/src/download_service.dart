import 'dart:convert';
import 'dart:io';

import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

import 'models.dart';

class DownloadService {
  Future<Directory> _dir() async {
    final base = await getApplicationDocumentsDirectory();
    final d = Directory('${base.path}/papers');
    if (!await d.exists()) await d.create(recursive: true);
    return d;
  }

  Future<File> fileFor(Paper p) async => File('${(await _dir()).path}/${p.fileName}');

  Future<bool> isDownloaded(Paper p) async => (await fileFor(p)).exists();

  Future<File> download(Paper p, {void Function(double)? onProgress}) async {
    final file = await fileFor(p);
    if (await file.exists()) return file;
    final client = http.Client();
    try {
      final req = http.Request('GET', Uri.parse(p.url))
        ..headers['User-Agent'] = 'Mozilla/5.0 (Android) EduPapers';
      final res = await client.send(req).timeout(const Duration(seconds: 30));
      if (res.statusCode != 200) {
        throw HttpException('Server returned ${res.statusCode}');
      }
      final total = res.contentLength ?? 0;
      final bytes = <int>[];
      await for (final chunk in res.stream) {
        bytes.addAll(chunk);
        if (total > 0) onProgress?.call(bytes.length / total);
      }
      if (bytes.length < 5 || ascii.decode(bytes.sublist(0, 4), allowInvalid: true) != '%PDF') {
        throw const FormatException('The file is not a valid PDF');
      }
      final tmp = File('${file.path}.part');
      await tmp.writeAsBytes(bytes, flush: true);
      await tmp.rename(file.path);
      await _saveMeta(p);
      return file;
    } finally {
      client.close();
    }
  }

  Future<void> delete(Paper p) async {
    final f = await fileFor(p);
    if (await f.exists()) await f.delete();
    final meta = await _meta();
    meta.remove(p.id);
    await _writeMeta(meta);
  }

  Future<File> _metaFile() async => File('${(await _dir()).path}/downloads.json');

  Future<Map<String, dynamic>> _meta() async {
    final f = await _metaFile();
    if (!await f.exists()) return {};
    try {
      return jsonDecode(await f.readAsString()) as Map<String, dynamic>;
    } catch (_) {
      return {};
    }
  }

  Future<void> _writeMeta(Map<String, dynamic> m) async =>
      (await _metaFile()).writeAsString(jsonEncode(m));

  Future<void> _saveMeta(Paper p) async {
    final m = await _meta();
    m[p.id] = DateTime.now().toIso8601String();
    await _writeMeta(m);
  }

  Future<Set<String>> downloadedIds() async => (await _meta()).keys.toSet();
}
