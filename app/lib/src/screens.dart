import 'dart:io';

import 'package:flutter/material.dart';
import 'package:pdfx/pdfx.dart';
import 'package:url_launcher/url_launcher.dart';

import 'catalog_service.dart';
import 'download_service.dart';
import 'models.dart';

const boardIcons = {
  'Karnataka SSLC': Icons.school,
  'Karnataka 2nd PUC': Icons.menu_book,
  'VTU Engineering': Icons.engineering,
};

class HomeShell extends StatefulWidget {
  final CatalogService catalog;
  final DownloadService downloads;
  const HomeShell({super.key, required this.catalog, required this.downloads});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  int _tab = 0;
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      await widget.catalog.loadLocal();
    } catch (e) {
      _error = 'Could not load catalog: $e';
    }
    if (mounted) setState(() => _loading = false);
    final changed = await widget.catalog.refresh();
    if (changed && mounted) setState(() {});
  }

  Future<void> _manualRefresh() async {
    final ok = await widget.catalog.refresh();
    if (!mounted) return;
    setState(() {});
    ScaffoldMessenger.of(context).showSnackBar(SnackBar(
      content: Text(ok
          ? 'Catalog updated: ${widget.catalog.papers.length} papers'
          : 'Catalog is up to date (${widget.catalog.papers.length} papers)'),
    ));
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Scaffold(body: Center(child: CircularProgressIndicator()));
    if (_error != null) return Scaffold(body: Center(child: Text(_error!)));
    final pages = [
      BrowsePage(
        papers: widget.catalog.papers,
        path: const [],
        downloads: widget.downloads,
        onRefresh: _manualRefresh,
      ),
      SearchPage(papers: widget.catalog.papers, downloads: widget.downloads),
      DownloadsPage(papers: widget.catalog.papers, downloads: widget.downloads),
      const AboutPage(),
    ];
    return Scaffold(
      body: IndexedStack(index: _tab, children: pages),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: const [
          NavigationDestination(icon: Icon(Icons.home_outlined), selectedIcon: Icon(Icons.home), label: 'Browse'),
          NavigationDestination(icon: Icon(Icons.search), label: 'Search'),
          NavigationDestination(icon: Icon(Icons.download_outlined), selectedIcon: Icon(Icons.download_done), label: 'Saved'),
          NavigationDestination(icon: Icon(Icons.info_outline), selectedIcon: Icon(Icons.info), label: 'About'),
        ],
      ),
    );
  }
}

/// Drills down board → stream → group → semester, skipping levels with a single value.
class BrowsePage extends StatelessWidget {
  final List<Paper> papers;
  final List<String> path;
  final int startLevel;
  final DownloadService downloads;
  final Future<void> Function()? onRefresh;
  const BrowsePage({
    super.key,
    required this.papers,
    required this.path,
    this.startLevel = 0,
    required this.downloads,
    this.onRefresh,
  });

  @override
  Widget build(BuildContext context) {
    var level = startLevel;
    var options = <String, int>{};
    while (level < browseLevels.length) {
      options = {};
      for (final p in papers) {
        final v = levelValue(p, browseLevels[level]);
        if (v.isNotEmpty) options[v] = (options[v] ?? 0) + 1;
      }
      if (options.length > 1 || (level == 0 && options.isNotEmpty)) break;
      level++;
    }
    final title = path.isEmpty ? 'Question Papers' : path.last;
    if (level >= browseLevels.length || options.isEmpty) {
      return PaperListPage(title: title, papers: papers, downloads: downloads, showBack: path.isNotEmpty);
    }
    final keys = options.keys.toList()..sort(_naturalCompare(browseLevels[level]));
    return Scaffold(
      appBar: AppBar(
        title: Text(title),
        actions: [
          if (onRefresh != null)
            IconButton(tooltip: 'Refresh catalog', icon: const Icon(Icons.refresh), onPressed: onRefresh),
        ],
      ),
      body: ListView(
        padding: const EdgeInsets.all(12),
        children: [
          if (path.isEmpty)
            const Padding(
              padding: EdgeInsets.fromLTRB(4, 0, 4, 12),
              child: Text('Previous year & model question papers for Karnataka students',
                  style: TextStyle(fontSize: 15)),
            ),
          for (final k in keys)
            Card(
              child: ListTile(
                leading: Icon(path.isEmpty ? (boardIcons[k] ?? Icons.folder) : Icons.folder_outlined,
                    color: Theme.of(context).colorScheme.primary),
                title: Text(k, style: const TextStyle(fontWeight: FontWeight.w600)),
                subtitle: Text('${options[k]} papers'),
                trailing: const Icon(Icons.chevron_right),
                onTap: () => Navigator.of(context).push(MaterialPageRoute(
                  builder: (_) => BrowsePage(
                    papers: papers.where((p) => levelValue(p, browseLevels[level]) == k).toList(),
                    path: [...path, k],
                    startLevel: level + 1,
                    downloads: downloads,
                  ),
                )),
              ),
            ),
        ],
      ),
    );
  }
}

int Function(String, String) _naturalCompare(String level) {
  final yearDesc = level == 'group';
  return (a, b) {
    final ya = RegExp(r'(19|20)\d\d').firstMatch(a)?.group(0);
    final yb = RegExp(r'(19|20)\d\d').firstMatch(b)?.group(0);
    if (yearDesc && ya != null && yb != null && ya != yb) return yb.compareTo(ya);
    if (a.startsWith('Other') != b.startsWith('Other')) return a.startsWith('Other') ? 1 : -1;
    final na = int.tryParse(RegExp(r'\d+').firstMatch(a)?.group(0) ?? '');
    final nb = int.tryParse(RegExp(r'\d+').firstMatch(b)?.group(0) ?? '');
    if (!yearDesc && na != null && nb != null && na != nb) return na.compareTo(nb);
    return a.compareTo(b);
  };
}

class PaperListPage extends StatelessWidget {
  final String title;
  final List<Paper> papers;
  final DownloadService downloads;
  final bool showBack;
  const PaperListPage({
    super.key,
    required this.title,
    required this.papers,
    required this.downloads,
    this.showBack = true,
  });

  @override
  Widget build(BuildContext context) {
    final sorted = [...papers]..sort((a, b) {
        final y = b.year.compareTo(a.year);
        return y != 0 ? y : a.subject.compareTo(b.subject);
      });
    return Scaffold(
      appBar: AppBar(title: Text(title)),
      body: ListView.separated(
        itemCount: sorted.length,
        separatorBuilder: (_, __) => const Divider(height: 1),
        itemBuilder: (_, i) => PaperTile(paper: sorted[i], downloads: downloads),
      ),
    );
  }
}

class PaperTile extends StatefulWidget {
  final Paper paper;
  final DownloadService downloads;
  final VoidCallback? onChanged;
  const PaperTile({super.key, required this.paper, required this.downloads, this.onChanged});

  @override
  State<PaperTile> createState() => _PaperTileState();
}

class _PaperTileState extends State<PaperTile> {
  bool _saved = false;
  double? _progress;

  @override
  void initState() {
    super.initState();
    widget.downloads.isDownloaded(widget.paper).then((v) {
      if (mounted) setState(() => _saved = v);
    });
  }

  Future<void> _open() async {
    final messenger = ScaffoldMessenger.of(context);
    final nav = Navigator.of(context);
    setState(() => _progress = 0);
    try {
      final file = await widget.downloads.download(widget.paper, onProgress: (p) {
        if (mounted) setState(() => _progress = p);
      });
      if (!mounted) return;
      setState(() {
        _progress = null;
        _saved = true;
      });
      widget.onChanged?.call();
      await nav.push(MaterialPageRoute(builder: (_) => PdfViewerPage(paper: widget.paper, file: file)));
    } catch (e) {
      if (!mounted) return;
      setState(() => _progress = null);
      messenger.showSnackBar(SnackBar(
        content: Text('Download failed: $e'),
        action: SnackBarAction(
          label: 'Open in browser',
          onPressed: () => launchUrl(Uri.parse(widget.paper.url), mode: LaunchMode.externalApplication),
        ),
      ));
    }
  }

  @override
  Widget build(BuildContext context) {
    final p = widget.paper;
    return ListTile(
      leading: const Icon(Icons.picture_as_pdf, color: Colors.redAccent),
      title: Text(p.title),
      subtitle: Text(p.subtitle),
      trailing: _progress != null
          ? SizedBox(width: 28, height: 28, child: CircularProgressIndicator(value: _progress == 0 ? null : _progress))
          : Icon(_saved ? Icons.offline_pin : Icons.download_outlined,
              color: _saved ? Colors.green : null),
      onTap: _progress == null ? _open : null,
    );
  }
}

class PdfViewerPage extends StatefulWidget {
  final Paper paper;
  final File file;
  const PdfViewerPage({super.key, required this.paper, required this.file});

  @override
  State<PdfViewerPage> createState() => _PdfViewerPageState();
}

class _PdfViewerPageState extends State<PdfViewerPage> {
  late final PdfControllerPinch _controller =
      PdfControllerPinch(document: PdfDocument.openFile(widget.file.path));

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text(widget.paper.title, maxLines: 1, overflow: TextOverflow.ellipsis),
        actions: [
          PdfPageNumber(
            controller: _controller,
            builder: (_, state, page, pages) => Center(
              child: Padding(
                padding: const EdgeInsets.only(right: 16),
                child: Text('$page / ${pages ?? 0}'),
              ),
            ),
          ),
        ],
      ),
      body: PdfViewPinch(
        controller: _controller,
        builders: PdfViewPinchBuilders<DefaultBuilderOptions>(
          options: const DefaultBuilderOptions(),
          errorBuilder: (_, error) => Center(child: Text('Cannot open PDF: $error')),
        ),
      ),
    );
  }
}

class SearchPage extends StatefulWidget {
  final List<Paper> papers;
  final DownloadService downloads;
  const SearchPage({super.key, required this.papers, required this.downloads});

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  String _q = '';
  String? _board;

  @override
  Widget build(BuildContext context) {
    final boards = widget.papers.map((p) => p.board).toSet().toList()..sort();
    final results = _q.trim().length < 2
        ? <Paper>[]
        : widget.papers.where((p) => (_board == null || p.board == _board) && p.matches(_q)).take(300).toList();
    return Scaffold(
      appBar: AppBar(title: const Text('Search papers')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 8, 12, 4),
            child: TextField(
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.search),
                hintText: 'Subject, code, year (e.g. Mathematics 2023)',
                border: OutlineInputBorder(),
              ),
              onChanged: (v) => setState(() => _q = v),
            ),
          ),
          SizedBox(
            height: 48,
            child: ListView(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 8),
              children: [
                Padding(
                  padding: const EdgeInsets.all(4),
                  child: ChoiceChip(label: const Text('All'), selected: _board == null, onSelected: (_) => setState(() => _board = null)),
                ),
                for (final b in boards)
                  Padding(
                    padding: const EdgeInsets.all(4),
                    child: ChoiceChip(label: Text(b), selected: _board == b, onSelected: (_) => setState(() => _board = b)),
                  ),
              ],
            ),
          ),
          Expanded(
            child: results.isEmpty
                ? Center(child: Text(_q.trim().length < 2 ? 'Type at least 2 letters' : 'No papers found'))
                : ListView.builder(
                    itemCount: results.length,
                    itemBuilder: (_, i) => PaperTile(
                      key: ValueKey(results[i].id),
                      paper: results[i],
                      downloads: widget.downloads,
                    ),
                  ),
          ),
        ],
      ),
    );
  }
}

class DownloadsPage extends StatefulWidget {
  final List<Paper> papers;
  final DownloadService downloads;
  const DownloadsPage({super.key, required this.papers, required this.downloads});

  @override
  State<DownloadsPage> createState() => _DownloadsPageState();
}

class _DownloadsPageState extends State<DownloadsPage> {
  List<Paper> _saved = [];

  Future<void> _reload() async {
    final ids = await widget.downloads.downloadedIds();
    if (mounted) setState(() => _saved = widget.papers.where((p) => ids.contains(p.id)).toList());
  }

  @override
  void initState() {
    super.initState();
    _reload();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Saved for offline'),
        actions: [IconButton(icon: const Icon(Icons.refresh), onPressed: _reload)],
      ),
      body: RefreshIndicator(
        onRefresh: _reload,
        child: _saved.isEmpty
            ? ListView(children: const [
                SizedBox(height: 120),
                Center(child: Text('Papers you open are saved here for offline use.')),
              ])
            : ListView.builder(
                itemCount: _saved.length,
                itemBuilder: (_, i) {
                  final p = _saved[i];
                  return Dismissible(
                    key: ValueKey(p.id),
                    direction: DismissDirection.endToStart,
                    background: Container(
                      color: Colors.red,
                      alignment: Alignment.centerRight,
                      padding: const EdgeInsets.only(right: 20),
                      child: const Icon(Icons.delete, color: Colors.white),
                    ),
                    onDismissed: (_) async {
                      await widget.downloads.delete(p);
                      _reload();
                    },
                    child: PaperTile(paper: p, downloads: widget.downloads),
                  );
                },
              ),
      ),
    );
  }
}

class AboutPage extends StatelessWidget {
  const AboutPage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('About')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Karnataka Question Papers', style: TextStyle(fontSize: 20, fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          const Text(
            'Free previous-year and model question papers for Karnataka SSLC, 2nd PUC '
            '(Science, Commerce, Arts) and VTU engineering students.',
          ),
          const SizedBox(height: 16),
          const Text('Disclaimer', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 4),
          const Text(
            'This app is not affiliated with KSEAB, the Department of Pre-University Education, '
            'or VTU. Papers are linked from their publicly available sources and remain the '
            'property of the respective boards. The source of every paper is recorded in the catalog.',
          ),
          const SizedBox(height: 16),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.privacy_tip_outlined),
            title: const Text('Privacy policy'),
            onTap: () => launchUrl(
              Uri.parse('https://github.com/hklikhithgowdaliki-debug/Education-App/blob/main/PRIVACY_POLICY.md'),
              mode: LaunchMode.externalApplication,
            ),
          ),
          ListTile(
            contentPadding: EdgeInsets.zero,
            leading: const Icon(Icons.bug_report_outlined),
            title: const Text('Report a broken paper'),
            onTap: () => launchUrl(
              Uri.parse('https://github.com/hklikhithgowdaliki-debug/Education-App/issues'),
              mode: LaunchMode.externalApplication,
            ),
          ),
        ],
      ),
    );
  }
}
