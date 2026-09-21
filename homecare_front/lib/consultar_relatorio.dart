import 'dart:convert';

import 'package:app/api.dart';
import 'package:app/logout_button.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ConsultarRelatorio extends StatefulWidget {
  final String token;

  const ConsultarRelatorio({super.key, required this.token});

  @override
  State<ConsultarRelatorio> createState() => _ConsultarRelatorioState();
}

class _ConsultarRelatorioState extends State<ConsultarRelatorio> {
  Map<int, List> relatoriosPorPaciente = {};
  List relatorios = [];
  String msg = '';

  @override
  void initState() {
    super.initState();
    buscarRelatorios();
  }

  Future<void> buscarRelatorios() async {
    final url = Uri.parse('$baseUrl/relatorios_diarios');

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
            relatorios = [];
            relatoriosPorPaciente = {};
            msg = dados['msg'] ?? 'Nenhum relatório encontrado.';
          });
        } else {
          setState(() {
            relatorios = List.from(lista);
            relatoriosPorPaciente = {};
            msg = '';

            for (final relatorio in relatorios) {
              final pacienteId = relatorio['paciente']['id'];

              if (!relatoriosPorPaciente.containsKey(pacienteId)) {
                relatoriosPorPaciente[pacienteId] = [];
              }

              relatoriosPorPaciente[pacienteId]!.add(relatorio);
            }
          });
        }
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Consultar relatórios'),
        actions: [LogoutButton()],
      ),

      body: relatoriosPorPaciente.isEmpty
          ? Center(child: Text(msg))
          : ListView(
              padding: const EdgeInsets.all(20),

              children: relatoriosPorPaciente.entries.map<Widget>((entry) {
                final relatorioPaciente = entry.value;

                final pacienteNome =
                    relatorioPaciente.first['paciente']['nome'];

                final pacienteId = relatorioPaciente.first['paciente']['id'];

                return Card(
                  child: ExpansionTile(
                    title: Text(
                      'Paciente: $pacienteNome - ID: $pacienteId',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                      ),
                    ),

                    subtitle: Text(
                      relatorioPaciente.length == 1
                          ? '1 relatório'
                          : '${relatorioPaciente.length} relatórios',
                    ),

                    children: relatorioPaciente.map<Widget>((relatorio) {
                      return ExpansionTile(
                        title: Text(
                          'Relatório feito em: ${relatorio['data_horario']}',
                          style: const TextStyle(fontWeight: FontWeight.w600),
                        ),

                        subtitle: Text(
                          'Responsável: ${relatorio['responsavel']['nome']}',
                        ),

                        children: [
                          Padding(
                            padding: const EdgeInsets.all(16),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Text(
                                  'Alimentação: ${relatorio['alimentacao'] ?? 'Não informado'}',
                                ),

                                Text(
                                  'Higiene: ${relatorio['higiene'] ?? 'Não informado'}',
                                ),

                                Text(
                                  'Glicemia: ${relatorio['glicemia'] ?? 'Não informado'}',
                                ),

                                Text(
                                  'Temperatura: ${relatorio['temperatura'] ?? 'Não informado'}',
                                ),

                                Text(
                                  'Pressão arterial: ${relatorio['pressao_arterial'] ?? 'Não informado'}',
                                ),

                                Text(
                                  'Observações: ${relatorio['obs'] ?? 'Não informado'}',
                                ),
                              ],
                            ),
                          ),
                        ],
                      );
                    }).toList(),
                  ),
                );
              }).toList(),
            ),
    );
  }
}
