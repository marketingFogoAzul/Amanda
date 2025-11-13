// java-modules/src/main/java/com/zipbum/Utilitarios.java
package com.zipbum;

import java.text.DecimalFormat;
import java.text.DecimalFormatSymbols;
import java.text.ParseException;
import java.util.Locale;

/**
 * Classe de Utilitários com métodos estáticos de ajuda
 * para os módulos de processamento.
 */
public class Utilitarios {

    /**
     * Limpa e converte uma string de moeda (ex: "R$ 1.000,50") para um double.
     * @param valorMoeda A string de moeda.
     * @return O valor como double.
     * @throws ParseException Se o formato for irreconhecível.
     */
    public static double parseMoedaParaDouble(String valorMoeda) throws ParseException {
        if (valorMoeda == null || valorMoeda.trim().isEmpty()) {
            return 0.0;
        }

        // Define os símbolos para o padrão Brasileiro (vírgula como decimal)
        DecimalFormatSymbols symbols = new DecimalFormatSymbols(new Locale("pt", "BR"));
        symbols.setDecimalSeparator(',');
        symbols.setGroupingSeparator('.');
        
        // Remove "R$" e espaços em branco
        String valorLimpo = valorMoeda.replace("R$", "").trim();

        // Tenta fazer o parse usando o formato monetário
        DecimalFormat df = new DecimalFormat("#,##0.00", symbols);
        df.setParseBigDecimal(false); // Parse como double

        try {
            return df.parse(valorLimpo).doubleValue();
        } catch (ParseException e) {
            // Se falhar, tenta um parse simples (ex: "1000.50")
            try {
                return Double.parseDouble(valorLimpo.replace(",", "."));
            } catch (NumberFormatException e2) {
                throw new ParseException("Formato de número ou moeda inválido: " + valorMoeda, 0);
            }
        }
    }

    /**
     * Função main para testar os utilitários
     * (Não é chamada pelo Flask, apenas para desenvolvimento)
     */
    public static void main(String[] args) {
        try {
            String teste1 = "R$ 1.000,50";
            String teste2 = "500,75";
            String teste3 = "1200.25";
            
            System.out.println(teste1 + " -> " + Utilitarios.parseMoedaParaDouble(teste1));
            System.out.println(teste2 + " -> " + Utilitarios.parseMoedaParaDouble(teste2));
            System.out.println(teste3 + " -> " + Utilitarios.parseMoedaParaDouble(teste3));
            
        } catch (ParseException e) {
            e.printStackTrace();
        }
    }
}