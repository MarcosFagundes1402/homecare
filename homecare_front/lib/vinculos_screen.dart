import 'dart:convert';

import 'package:app/paciente_detalhes.dart';
import 'package:flutter/material.dart';
import 'package:http/http.dart' as http;

class VinculosScreen extends StatefulWidget {
  final String token;

  const VinculosScreen({super.key, required this.token});

  @override
  State<VinculosScreen> createState() => _VinculosScreenState();
}

class _VinculosScreenState extends State<VinculosScreen> {
  Map<int, List> pacientesPorCuidador = {};
  List cuidadores = [];
  String msg = '';

  @override
  void initState() {
    super.initState();
    buscarCuidadores();
  }

  Future<void> buscarCuidadores() async {
    final url = Uri.parse('http://localhost:5000/cuidadores/consultar');

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
          cuidadores = List.from(dados);
        });
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  Future<void> buscarVinculo(int cuidadorID) async {
    final url = Uri.parse(
      'http://localhost:5000/cuidadores_pacientes/consultar-cuidador/$cuidadorID',
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
          if (dados is List) {
            pacientesPorCuidador[cuidadorID] = List.from(dados);
          } else {
            pacientesPorCuidador[cuidadorID] = [];
          }
        });
      }
    } catch (erro) {
      debugPrint('erro: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ver vínculos')),
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),
              child: Card(
                child: Column(
                  children: cuidadores.map<Widget>((cuidador) {
                    final pacientes =
                        pacientesPorCuidador[cuidador['id']] ?? [];

                    return ExpansionTile(
                      title: Text(
                        'Cuidador: ${cuidador['nome']}',
                        style: TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                      subtitle: Text('ID: ${cuidador['id']}'),
                      trailing: Text('${cuidador['status']}'),
                      onExpansionChanged: (aberto) {
                        if (aberto) {
                          buscarVinculo(cuidador['id']);
                        }
                      },
                      children: pacientes.isEmpty
                          ? const [
                              ListTile(
                                title: Text('Nenhum paciente vinculado.'),
                              ),
                            ]
                          : pacientes.map<Widget>((paciente) {
                              return ListTile(
                                title: Text('Paciente: ${paciente['nome']}'),
                                subtitle: Text('ID: ${paciente['id']}'),
                                trailing: const Icon(Icons.arrow_forward_ios),
                                onTap: () {
                                  Navigator.push(
                                    context,
                                    MaterialPageRoute(
                                      builder: (context) => PacienteDetalhes(
                                        paciente: paciente,
                                        token: widget.token,
                                        modoAdmin: true,
                                      ),
                                    ),
                                  );
                                },
                              );
                            }).toList(),
                    );
                  }).toList(),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
