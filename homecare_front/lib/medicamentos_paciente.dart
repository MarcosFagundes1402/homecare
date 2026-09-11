import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class MedicamentosPaciente extends StatefulWidget {
  final String pacienteNome;
  final int pacienteId;
  final String token;

  const MedicamentosPaciente({
    super.key,
    required this.pacienteNome,
    required this.pacienteId,
    required this.token,
  });

  @override
  State<MedicamentosPaciente> createState() => _MedicamentosPacienteState();
}

class _MedicamentosPacienteState extends State<MedicamentosPaciente> {
  List medicamentos = [];
  String msg = "";

  @override
  void initState() {
    super.initState();
    buscarMedicamentos();
  }

  Future<void> buscarMedicamentos() async {
    final url = Uri.parse(
      'http://localhost:5000/medicamentos/consultar-paciente/${widget.pacienteId}',
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
        final lista = dados['medicamentos'] ?? [];

        if (!mounted) return;

        setState(() {
          medicamentos = lista;
          msg = lista.isEmpty
              ? dados['msg'] ?? 'Nenhum medicamento encontrado.'
              : '';
        });
      } else {
        final dados = jsonDecode(response.body);

        if (!mounted) return;

        setState(() {
          msg = dados['msg'] ?? 'Erro ao buscar medicamentos.';
        });
      }
    } catch (erro) {
      if (!mounted) return;
      setState(() {
        msg = 'Não foi possivel conectar ao servidor';
      });

      debugPrint('Erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text('Medicações de: ${widget.pacienteNome}')),

      body: medicamentos.isEmpty
          ? Center(child: Text(msg.isEmpty ? 'Carregando...' : msg))
          : ListView.builder(
              itemCount: medicamentos.length,
              itemBuilder: (context, index) {
                final medicamento = medicamentos[index];

                return Card(
                  child: ExpansionTile(
                    title: Text(medicamento['nome'] ?? 'Medicamento sem nome'),
                    subtitle: Text(
                      'Dosagem: ${medicamento['dosagem']} '
                      ' Horário: ${medicamento['horario']}'
                      ' Status: ${medicamento['status']}',
                    ),
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.center,
                          children: [Text('Observações: ${medicamento['obs'] ?? 'Sem observações'}')],
                        ),
                      ),
                    ],
                  ),
                );
              },
            ),
    );
  }
}
