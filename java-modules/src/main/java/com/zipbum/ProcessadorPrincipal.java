// java-modules/src/main/java/com/zipbum/ProcessadorPrincipal.java
package com.zipbum;

import java.util.Arrays;

/**
 * Classe principal (Main) que o Flask irá chamar.
 * Ela atua como um roteador, decidindo qual módulo executar 
 * com base no primeiro argumento (ex: "fiscal" ou "csv").
 */
public class ProcessadorPrincipal {

    public static void main(String[] args) {
        if (args.length == 0) {
            System.err.println("Erro: Nenhum comando fornecido (ex: 'fiscal' ou 'csv').");
            System.exit(1);
        }

        String comando = args[0];
        // Cria um novo array de argumentos sem o primeiro comando
        String[] moduloArgs = Arrays.copyOfRange(args, 1, args.length);

        try {
            switch (comando.toLowerCase()) {
                case "fiscal":
                    // Chama o main da CalculadoraFiscal
                    CalculadoraFiscal.main(moduloArgs);
                    break;

                case "csv":
                    // Chama o main do ValidadorCSV
                    ValidadorCSV.main(moduloArgs);
                    break;
                
                // (Adicionar outros módulos aqui)
                
                default:
                    System.err.println("Erro: Comando desconhecido: " + comando);
                    System.exit(1);
            }
        } catch (Exception e) {
            System.err.println("Erro fatal no processador principal: " + e.getMessage());
            e.printStackTrace();
            System.exit(1);
        }
    }
}