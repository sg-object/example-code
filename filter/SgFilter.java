package com.example.demo.config;

import java.io.IOException;
import java.util.Arrays;
import java.util.List;
import org.springframework.http.MediaType;
import org.springframework.stereotype.Component;
import org.springframework.util.AntPathMatcher;
import org.springframework.web.filter.OncePerRequestFilter;
import com.fasterxml.jackson.databind.ObjectMapper;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import lombok.Builder;
import lombok.Getter;

@Component
public class SgFilter extends OncePerRequestFilter {

	final List<String> patterns = Arrays.asList("/swagger-ui/**", "/v3/api-docs/**");

	final AntPathMatcher pathMatcher = new AntPathMatcher();

	final ObjectMapper mapper = new ObjectMapper();

	final String APPLICATION_JSON = MediaType.APPLICATION_JSON_VALUE;

	@Override
	protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
			throws ServletException, IOException {
		final SgResponseWrapper responseWrapper = new SgResponseWrapper(response);
		filterChain.doFilter(request, responseWrapper);

		final String body = responseWrapper.getBody();
		Object content;

		if (response.getContentType().startsWith(APPLICATION_JSON)) {
			content = this.mapper.readTree(body);
		} else {
			content = body;
		}
		var sgResponse = SgResponse.builder().code("success").content(content).build();
		var res = this.mapper.writeValueAsBytes(sgResponse);

		response.setContentLength(res.length);
		response.getOutputStream().write(res);
		response.flushBuffer();
	}

	@Override
	protected boolean shouldNotFilter(HttpServletRequest request) throws ServletException {
		final var path = request.getServletPath();
		return patterns.stream().anyMatch(pattern -> pathMatcher.match(pattern, path));
	}

	@Getter
	@Builder
	static class SgResponse {
		private String code;
		private Object content;
	}
}
