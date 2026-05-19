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

@RestController
@RequestMapping("/geo")
public class GeoProxyController {

    @Value("${geo.python.api.url:http://localhost:8000/api/v1}")
    private String pythonApiUrl;

    private final RestTemplate restTemplate;

    public GeoProxyController(RestTemplate restTemplate) {
        this.restTemplate = restTemplate;
    }

    @RequestMapping(value = "/**", method = {RequestMethod.GET, RequestMethod.POST, RequestMethod.PUT,
            RequestMethod.DELETE, RequestMethod.PATCH})
    public ResponseEntity<?> proxy(HttpServletRequest request, @RequestBody(required = false) String body) {
        String path = extractGeoPath(request);
        String queryString = request.getQueryString();
        String url = pythonApiUrl + path + (queryString != null && !queryString.isEmpty() ? "?" + queryString : "");

        HttpMethod method = HttpMethod.valueOf(request.getMethod());
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        //发送代理请求到Python API
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
            return handlePythonError(e.getResponseBodyAsString(), e.getStatusCode().value());
        } catch (HttpServerErrorException e) {
            return handlePythonError(e.getResponseBodyAsString(), e.getStatusCode().value());
        } catch (Exception e) {
            return ResponseEntity.ok(AjaxResult.error("代理请求失败: " + e.getMessage()));
        }
    }

    //从请求路径中提取Geo API路径
    private String extractGeoPath(HttpServletRequest request) {
        String fullPath = request.getRequestURI();
        int geoIndex = fullPath.indexOf("/geo");
        if (geoIndex >= 0) {
            return fullPath.substring(geoIndex + 4);
        }
        return fullPath;
    }

    //处理Python API错误
    private ResponseEntity<AjaxResult> handlePythonError(String errorBody, int statusCode) {
        String detail = "Python API 错误 (HTTP " + statusCode + ")";
        if (errorBody != null && !errorBody.isEmpty()) {
            try {
                JSONObject errorJson = JSON.parseObject(errorBody);
                detail = errorJson.containsKey("detail") ? errorJson.getString("detail") : errorBody;
            } catch (Exception e) {
                detail = errorBody;
            }
        }
        return ResponseEntity.ok(AjaxResult.error(statusCode, detail));
    }
}
