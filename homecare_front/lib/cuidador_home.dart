import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:http/http.dart' as htpp;
import 'package:app/paciente_detalhes.dart';

class CuidadorHome extends StatefulWidget {
  final String nome;
  final String token;

  const CuidadorHome({super.key, required this.nome, required this.token});

  @override
  State<CuidadorHome> createState() => _CuidadorHomeState();
}

class _CuidadorHomeState extends State<CuidadorHome> {
  List pacientes = [];

  @override
  void initState() {
    super.initState();
    buscarPacientes();
  }

  Future<void> buscarPacientes() async {
    final url = Uri.parse(
      'http://localhost:5000/cuidadores_pacientes/meus-pacientes',
    );

    try {
      final response = await htpp.get(
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
          pacientes = dados;
        });
      }
      debugPrint('STATUS PACIENTE: ${response.statusCode}');
      debugPrint('BODY PACIENTE: ${response.body}');
    } catch (erro) {
      debugPrint('ERRO: $erro');
    }
  }

  @override
  Widget build(BuildContext context) {
    final pacientesVisiveis = pacientes.take(3).toList();

    return Scaffold(
      appBar: AppBar(title: const Text('Home Cuidador')),

      //CARD DE BEM-VINDO
      body: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Center(
            child: Text(
              'Bem-vindo, ${widget.nome}',
              textAlign: TextAlign.center,
              style: const TextStyle(fontSize: 30, fontWeight: FontWeight.bold),
            ),
          ),

          const SizedBox(height: 50),

          //CARD DE MEUS PACIENTES
          Center(
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 500),

              child: Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.center,
                    children: [
                      const Text(
                        'Meus pacientes',
                        style: TextStyle(
                          fontSize: 25,
                          fontWeight: FontWeight.w600,
                        ),
                      ),

                      const SizedBox(height: 10),

                      ...pacientesVisiveis.map((pacientes) {
                        return ListTile(
                          contentPadding: EdgeInsets.only(top: 5),
                          title: Text(
                            'Nome: ${pacientes['nome']}',
                            style: TextStyle(
                              fontSize: 17,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          subtitle: Column(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Text('Contato: +55 ${pacientes['tel']}'),
                              Text('Status: ${pacientes['status']}'),
                            ],
                          ),
                          trailing: const Icon(Icons.arrow_forward_ios),
                          onTap: () {
                            // ABRIR DETALHES DO PACIENTE
                            Navigator.push(
                              context,
                              MaterialPageRoute(builder: (context) => PacienteDetalhes(
                                paciente: pacientes,
                                token: widget.token,
                              )
                              )
                            );
                          },
                        );
                      }),

                      if (pacientes.length > 2)
                        TextButton(
                          onPressed: () {},
                          child: const Text('Ver mais...'),
                        ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }
}
