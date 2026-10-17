import 'dart:convert';
import 'dart:io';

import 'package:flutter/services.dart' show rootBundle;
import 'package:http/http.dart' as http;
import 'package:path_provider/path_provider.dart';

import 'models.dart';

const catalogUrl =
    'https://raw.githubusercontent.com/hklikhithgowdaliki-debug/Education-App/main/data/catalog.json';

class CatalogService {
  List<Paper> papers = [];
  DateTime? updatedAt;

  Future<File> _cacheFile() async {
    final dir = await getApplicationSupportDirectory();
    return File('${dir.path}/catalog.json');
  }

  List<Paper> _parse(String body) {
    final decoded = jsonDecode(body);
    final list = decoded is Map ? decoded['papers'] as List : decoded as List;
    return list.map((e) => Paper.fromJson(e as Map<String, dynamic>)).toList();
  }

  /// Loads the cached catalog (or the bundled copy) immediately.
  Future<void> loadLocal() async {
    final cache = await _cacheFile();
    if (await cache.exists()) {
      try {
        papers = _parse(await cache.readAsString());
        updatedAt = await cache.lastModified();
        return;
      } catch (_) {}
    }
    papers = _parse(await rootBundle.loadString('assets/catalog.json'));
  }

  /// Fetches the latest catalog from GitHub. Returns true when it changed.
  Future<bool> refresh() async {
    try {
      final res = await http.get(Uri.parse(catalogUrl)).timeout(const Duration(seconds: 20));
      if (res.statusCode != 200) return false;
      final fresh = _parse(res.body);
      if (fresh.isEmpty) return false;
      await (await _cacheFile()).writeAsString(res.body);
      final changed = fresh.length != papers.length;
      papers = fresh;
      updatedAt = DateTime.now();
      return changed;
    } catch (_) {
      return false;
    }
  }
}
