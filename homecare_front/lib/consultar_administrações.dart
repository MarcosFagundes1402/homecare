import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ConsultarAdministracoes extends StatefulWidget {
  final String token;

  const ConsultarAdministracoes({super.key, required this.token});

  @override
  State<ConsultarAdministracoes> createState() =>
      _ConsultarAdministracoesState();
}

class _ConsultarAdministracoesState extends State<ConsultarAdministracoes> {
  Map<int, List> administracoesPorPaciente = {};
  List administracoes = [];
  String msg = '';

  @override
  void initState() {
    super.initState();
    buscarAdministracoes();
  }

  Future<void> buscarAdministracoes() async {
    final url = Uri.parse('http://localhost:5000/administracao_medicamentos');

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
        final lista = dados['administracoes'] ?? [];

        if (!mounted) return;

        if (lista.isEmpty) {
          setState(() {
            administracoes = [];
            administracoesPorPaciente = {};
            msg = dados['msg'] ?? 'Nenhuma administração encontrada.';
          });
        } else {
          setState(() {
            administracoes = List.from(lista);
            administracoesPorPaciente = {};
            msg = '';

            for (final administracao in administracoes) {
              final pacienteId = administracao['paciente']['id'];

              if (!administracoesPorPaciente.containsKey(pacienteId)) {
                administracoesPorPaciente[pacienteId] = [];
              }

              administracoesPorPaciente[pacienteId]!.add(administracao);
            }
          });
        }
      }
    } catch (erro) {
      debugPrint('ERRO: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Consultar administrações')),

      body: administracoesPorPaciente.isEmpty
          ? Center(child: Text(msg))
          : ListView(
              padding: const EdgeInsets.all(20),

              children: administracoesPorPaciente.entries.map<Widget>((entry) {
                final administracaoPaciente = entry.value;

                final pacienteNome =
                    administracaoPaciente.first['paciente']['nome'];

                return Card(
                  child: ExpansionTile(
                    title: Text(
                      'Paciente: $pacienteNome',
                      style: const TextStyle(
                        fontSize: 20,
                        fontWeight: FontWeight.w600,
                      ),
                    ),

                    subtitle: Text(
                      administracaoPaciente.length == 1
                          ? '1 administração'
                          : '${administracaoPaciente.length} administrações',
                    ),
                    children: administracaoPaciente.map<Widget>((
                      administracao,
                    ) {
                      return Container(
                        margin: const EdgeInsets.symmetric(
                          horizontal: 12,
                          vertical: 6,
                        ),
                        decoration: BoxDecoration(
                          border: Border.all(color: const Color.fromARGB(73, 7, 7, 7)),
                          borderRadius: BorderRadius.circular(8),
                        ),
                        child: ListTile(
                          title: Text(
                            '${administracao['medicamento']['nome']} - ${administracao['horario_administrado']}',
                            style: TextStyle(
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          subtitle: Text(
                            'Administrado por: ${administracao['responsavel']['nome']}\n'
                            'Dosagem: ${administracao['dosagem_administrada']}\n'
                            'Horário previsto: ${administracao['horario_previsto'] ?? 'Não informado'}\n'
                            'Observações: ${administracao['obs'] ?? 'Sem observação'}'
                          ),
                          trailing: Text('${administracao['status']}'),
                        ),
                      );
                    }).toList(),
                  ),
                );
              }).toList(),
            ),
    );
  }
}
