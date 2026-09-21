import 'dart:convert';

import 'package:app/api.dart';
import 'package:app/logout_button.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class ConsultarMadicamentos extends StatefulWidget {
  final String token;

  const ConsultarMadicamentos({super.key, required this.token});

  @override
  State<ConsultarMadicamentos> createState() => _ConsultarMedicamentosState();
}

class _ConsultarMedicamentosState extends State<ConsultarMadicamentos> {
  List medicamentos = [];
  List pacientes = [];

  @override
  void initState() {
    super.initState();

    buscarMedicamentos();
    buscarPacientes();
  }

  Future<void> buscarMedicamentos() async {
    final url = Uri.parse('$baseUrl/medicamentos/consultar');

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
          medicamentos = List.from(dados['medicamentos'] ?? []);
        });
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
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

        setState(() {
          pacientes = List.from(dados);
        });
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  String buscarNomePaciente(int pacienteId) {
    final paciente = pacientes.where((p) => p['id'] == pacienteId);

    if (paciente.isEmpty) {
      return 'Paciente não encontrado';
    }

    return paciente.first['nome'];
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Consultar todos os medicamentos'),
        actions: const [LogoutButton()],
      ),
      body: medicamentos.isEmpty
          ? const Center(child: Text('Nenhum medicamento encontrado.'))
          : ListView.builder(
              padding: const EdgeInsets.all(20),
              itemCount: medicamentos.length,
              itemBuilder: (context, index) {
                final medicamento = medicamentos[index];

                return Card(
                  child: ListTile(
                    title: Text(
                      medicamento['nome'],
                      style: const TextStyle(fontWeight: FontWeight.w600),
                    ),
                    subtitle: Text(
                      'Paciente: ${buscarNomePaciente(medicamento['paciente_id'])}\n'
                      'Dosagem: ${medicamento['dosagem']}\n'
                      'Horário: ${medicamento['horario']}',
                    ),
                    trailing: Text('${medicamento['status']}'),
                  ),
                );
              },
            ),
    );
  }
}
