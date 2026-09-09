import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class MinhasAdministracoes extends StatefulWidget {
  final String nome;
  final String token;
  final int? pacienteId;

  const MinhasAdministracoes({
    super.key,
    required this.nome,
    required this.token,
    this.pacienteId,
  });

  @override
  State<MinhasAdministracoes> createState() => _MinhasAdministracoesState();
}

class _MinhasAdministracoesState extends State<MinhasAdministracoes> {
  List administracoes = [];
  bool carregando = true;

  @override
  void initState() {
    super.initState();
    buscarAdministracoes();
  }

  Future<void> buscarAdministracoes() async {
    final url = Uri.parse(
      'http://localhost:5000/administracao_medicamentos/paciente/meu-historico',
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

        if (!mounted) return;

        setState(() {
          administracoes = dados['administracoes'];
          carregando = false;
        });
      }

      debugPrint('Body: ${response.body}');
    } catch (erro) {
      debugPrint('ERRO RELATORIOS: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    final administracoesVisiveis = administracoes.take(5).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Voltar - Home Paciente')),

      //CARD MEU HISTORICO DE ADMINISTRACOES
      body: ListView(
        padding: const EdgeInsets.fromLTRB(20, 50, 20, 20),
        children: [
          const Center(
            child: Text(
              'Meu histórico de administrações',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 26, fontWeight: FontWeight.w600),
            ),
          ),

          const SizedBox(height: 50),

          ...administracoesVisiveis.map((administracao) {
            return Card(
              child: ExpansionTile(
                leading: const Icon(Icons.medication),
                title: Text(
                  administracao['horario_administrado'],
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),

                subtitle: Text(
                  'Administrado por: ${administracao['responsavel']['nome']}',
                ),

                children: [
                  const Divider(),

                  Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.stretch,
                      children: [
                        Text(
                          'Medicamento: ${administracao['medicamento']['nome']}',
                        ),
                        SizedBox(height: 8),

                        Text(
                          'Dosagem Administrada: ${administracao['dosagem_administrada']}',
                        ),
                        SizedBox(height: 8),

                        Text(
                          'Horário Previsto: ${administracao['horario_previsto']}',
                        ),
                        SizedBox(height: 8),

                        Text('Status: ${administracao['status']}'),
                        SizedBox(height: 8),

                        Text('Observação: ${administracao['obs']}'),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
