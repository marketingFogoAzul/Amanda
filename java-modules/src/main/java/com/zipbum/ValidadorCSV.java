// java-modules/src/main/java/com/zipbum/ValidadorCSV.java
package com.zipbum;

import org.apache.commons.csv.CSVFormat;
import org.apache.commons.csv.CSVParser;
import org.apache.commons.csv.CSVRecord;

import java.io.FileReader;
import java.io.Reader;
import java.util.Map;

/**
 * Módulo para validação pesada de arquivos CSV (planilhas).
 * Verifica a estrutura, tipos de dados e regras de negócio.
 */
public class ValidadorCSV {

    /**
     * Valida um arquivo CSV.
     * @param caminhoArquivo O caminho para o arquivo .csv no servidor.
     * @param colunasEsperadas O número de colunas que cada linha deve ter.
     * @return Uma string "VALIDO" ou uma mensagem de erro.
     */
    public String validar(String caminhoArquivo, int colunasEsperadas) {
        long linhaAtual = 1;
        try (
            Reader reader = new FileReader(caminhoArquivo);
            CSVParser csvParser = new CSVParser(reader, CSVFormat.DEFAULT
                    .withHeader() // Assume que a primeira linha é o cabeçalho
                    .withDelimiter(';')
                    .withIgnoreEmptyLines(true))
        ) {

            Map<String, Integer> headerMap = csvParser.getHeaderMap();
            
            for (CSVRecord csvRecord : csvParser) {
                linhaAtual = csvRecord.getRecordNumber() + 1; // +1 por causa do header

                if (csvRecord.size() != colunasEsperadas) {
                    return String.format("Erro na linha %d: Número de colunas incorreto. (Esperado: %d, Encontrado: %d)",
                            linhaAtual, colunasEsperadas, csvRecord.size());
                }
                
                if (headerMap.containsKey("preco")) {
                    String precoStr = csvRecord.get("preco");
                    if (precoStr == null || precoStr.trim().isEmpty()) {
                        return String.format("Erro na linha %d: Coluna 'preco' está vazia.", linhaAtual);
                    }
                    
                    try {
                        Double.parseDouble(precoStr.replace(",", "."));
                    } catch (NumberFormatException e) {
                        return String.format("Erro na linha %d: Coluna 'preco' não é um número válido (%s).", linhaAtual, precoStr);
                    }
                }
            }

        } catch (Exception e) {
            return String.format("Erro ao processar o arquivo: %s (Linha aprox. %d)", e.getMessage(), linhaAtual);
        }
        
        return "VALIDO"; // Se chegou até aqui, está tudo certo.
    }

    /**
     * Ponto de entrada para o Flask.
     */
    public static void main(String[] args) {
        // [0]=caminhoArquivo, [1]=colunasEsperadas
        if (args.length < 2) {
            System.err.println("Erro: Argumentos insuficientes para validação CSV. (Esperado: Caminho_Arquivo Colunas)");
            System.exit(1);
        }
        
        try {
            String caminhoArquivo = args[0];
            int colunas = Integer.parseInt(args[1]);
            
            ValidadorCSV validador = new ValidadorCSV();
            String resultado = validador.validar(caminhoArquivo, colunas);
            
            // Retorna o resultado para o Python (stdout)
            System.out.println(resultado);
            System.exit(0);

        } catch (NumberFormatException e) {
            System.err.println("Erro: Número de colunas esperado inválido.");
            System.exit(1);
        } catch (Exception e) {
            System.err.println("Erro na validação: " + e.getMessage());
            System.exit(1);
        }
    }
}