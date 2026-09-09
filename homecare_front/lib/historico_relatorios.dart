import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class HistoricoRelatorios extends StatefulWidget {
  final int pacienteId;
  final String token;

  const HistoricoRelatorios({
    super.key,
    required this.pacienteId,
    required this.token,
  });

  @override
  State<HistoricoRelatorios> createState() => _HistoricoRelatoriosState();
}

class _HistoricoRelatoriosState extends State<HistoricoRelatorios> {
  List relatorios = [];
  String msg = '';

  @override
  void initState() {
    super.initState();

    buscarHistorico();
  }

  //BUSCAR HISTORICOS DO PACIENTE
  Future<void> buscarHistorico() async {
    final url = Uri.parse(
      'http://localhost:5000/relatorios_diarios/paciente/${widget.pacienteId}',
    );

    try {
      final response = await http.get(
        url,
        headers: {
          'Authorization': 'Bearer ${widget.token}',
          'Content-Type': 'application/json',
        },
      );

      if (response.statusCode == 200) {
        final dados = jsonDecode(response.body);
        final lista = dados['relatorios'] ?? [];

        if (!mounted) return;

        if (lista.isEmpty) {
          setState(() {
            msg = dados['msg'] ?? 'Nenhum relatório encontrado.';
          });
        } else {
          setState(() {
            relatorios = lista;
            msg = '';
          });
        }
      }
    } catch (erro) {
      debugPrint('ERRO RELATORIO: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    //final pacientesVisiveis = pacientes.take(4).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Historico de relatórios')),

      body: relatorios.isEmpty
          ? Center(child: Text(msg))
          : ListView.builder(
              padding: const EdgeInsets.all(20),
              itemCount: relatorios.length,
              itemBuilder: (context, index) {
                final relatorio = relatorios[index];

                return Card(
                  child: ListTile(
                    title: Text(
                      'Relatório: ${relatorio['data_horario']}',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                      ),
                    ),
                    subtitle: Text(
                      'Higiene: ${relatorio['higiene']}'
                      '\nAlimentação: ${relatorio['higiene']}'
                      '\nObservações: ${relatorio['observacoes']}'
                      '\nGlicemia: ${relatorio['glicemia']}'
                      '\nTemperatura: ${relatorio['temperatura']}'
                      '\nPressão Arterial: ${relatorio['pressao_arterial']}'
                    ),
                  ),
                );
              },
            ),
    );
  }
}
