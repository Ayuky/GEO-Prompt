package com.ruoyi.web.controller.geo;

import jakarta.servlet.http.HttpServletRequest;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestMethod;
import org.springframework.web.bind.annotation.RestController;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.HttpServerErrorException;
import org.springframework.web.client.RestTemplate;
import com.alibaba.fastjson2.JSON;
import com.alibaba.fastjson2.JSONObject;
import com.ruoyi.common.core.domain.AjaxResult;

import java.nio.charset.StandardCharsets;
import java.util.Base64;

@RestController
@RequestMapping("/geo/langfuse")
public class LangfuseProxyController {

    @Value("${langfuse.base-url:http://localhost:3000}")
    private String langfuseBaseUrl;

    @Value("${langfuse.public-key}")
    private String publicKey;

    @Value("${langfuse.secret-key}")
    private String secretKey;

    private final RestTemplate restTemplate;

    public LangfuseProxyController(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @RequestMapping(value = "/**", method = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT,
            RequestMethod.DELETE, RequestMethod.PATCH})
    public ResponseEntity<?> proxy(HttpServletRequest request, @RequestBody(required = false) String body) {
        String path = extractLangfusePath(request);
        String queryString = request.getQueryString();
        String url = langfuseBaseUrl + path + (queryString != null && !queryString.isEmpty() ? "?" + queryString : "");

        HttpMethod method = HttpMethod.valueOf(request.getMethod());
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        String auth = publicKey + ":" + secretKey;
        String encodedAuth = Base64.getEncoder().encodeToString(auth.getBytes(StandardCharsets.UTF_8));
        headers.set("Authorization", "Basic " + encodedAuth);

        try {
            HttpEntity<String> entity = new HttpEntity<>(body, headers);
            ResponseEntity<byte[]> response = restTemplate.exchange(url, method, entity, byte[].class);

            MediaType contentType = response.getHeaders().getContentType();
            if (contentType != null && !contentType.isCompatibleWith(MediaType.APPLICATION_JSON)) {
                return ResponseEntity.status(response.getStatusCode())
                        .headers(response.getHeaders())
                        .body(response.getBody());
            }

            byte[] rawBody = response.getBody();
            if (rawBody == null || rawBody.length == 0) {
                return ResponseEntity.ok().build();
            }
            String responseBody = new String(rawBody, StandardCharsets.UTF_8);
            return ResponseEntity.ok(JSON.parse(responseBody));
        } catch (HttpClientErrorException e) {
            return handleLangfuseError(e.getResponseBodyAsString(), e.getStatusCode().value());
        } catch (HttpServerErrorException e) {
            return handleLangfuseError(e.getResponseBodyAsString(), e.getStatusCode().value());
        } catch (Exception e) {
            return ResponseEntity.ok(AjaxResult.error("Langfuse 代理请求失败: " + e.getMessage()));
        }
    }

    private String extractLangfusePath(HttpServletRequest request) {
        String fullPath = request.getRequestURI();
        int langfuseIndex = fullPath.indexOf("/geo/langfuse");
        if (langfuseIndex >= 0) {
            return fullPath.substring(langfuseIndex + 13);
        }
        return fullPath;
    }

    private ResponseEntity<AjaxResult> handleLangfuseError(String errorBody, int statusCode) {
        String detail = "Langfuse API 错误 (HTTP " + statusCode + ")";
        if (errorBody != null && !errorBody.isEmpty()) {
            try {
                JSONObject errorJson = JSON.parseObject(errorBody);
                detail = errorJson.containsKey("message") ? errorJson.getString("message") : errorBody;
            } catch (Exception e) {
                detail = errorBody;
            }
        }
        return ResponseEntity.ok(AjaxResult.error(statusCode, detail));
    }
}
