import 'dart:convert';

import 'package:app/api.dart';
import 'package:app/logout_button.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ConsultarMedicamentoIndividual extends StatefulWidget {
  final String token;

  const ConsultarMedicamentoIndividual({super.key, required this.token});

  @override
  State<ConsultarMedicamentoIndividual> createState() => _ConsultarState();
}

class _ConsultarState extends State<ConsultarMedicamentoIndividual> {
  List pacientes = [];
  Map<int, List> medicamentosPorPaciente = {};

  @override
  void initState() {
    super.initState();

    buscarPacientes();
  }

  Future<void> buscarPacientes() async {
    final url = Uri.parse('$baseUrl/pacientes/consultar');

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

        final listaPacientes = List.from(dados);

        setState(() {
          pacientes = listaPacientes;
        });

        for (final paciente in listaPacientes) {
          buscarMedicamentos(paciente['id']);
        }
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  Future<void> buscarMedicamentos(int pacienteID) async {
    final url = Uri.parse(
      '$baseUrl/medicamentos/consultar-paciente/$pacienteID',
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
          medicamentosPorPaciente[pacienteID] = List.from(
            dados['medicamentos'] ?? [],
          );
        });
      }
    } catch (erro) {
      debugPrint('statua: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Consultar medicamentos'),
        actions: const [LogoutButton()],
      ),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: pacientes.map<Widget>((paciente) {
          final medicamentos = medicamentosPorPaciente[paciente['id']] ?? [];

          return Card(
            child: ExpansionTile(
              title: Text(
                'Paciente: ${paciente['nome']}',
                style: const TextStyle(
                  fontSize: 22,
                  fontWeight: FontWeight.w600,
                ),
              ),
              subtitle: Text(
                medicamentos.isEmpty
                    ? 'Sem medicamentos'
                    : medicamentos.length == 1
                    ? '1 medicamento'
                    : '${medicamentos.length} medicamentos',
              ),

              children: medicamentos.isEmpty
                  ? const [
                      ListTile(title: Text('Nenhum medicamento cadastrado.')),
                    ]
                  : medicamentos.map<Widget>((medicamento) {
                      return ListTile(
                        title: Text(medicamento['nome']),
                        subtitle: Text(
                          'Dosagem: ${medicamento['dosagem']}\n'
                          'Horário: ${medicamento['horario']}',
                        ),
                        trailing: Text('${medicamento['status']}'),
                      );
                    }).toList(),
            ),
          );
        }).toList(),
      ),
    );
  }
}
