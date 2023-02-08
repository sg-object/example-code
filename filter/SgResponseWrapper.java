package com.example.demo.config;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.http.HttpServletResponse;
import jakarta.servlet.http.HttpServletResponseWrapper;

public class SgResponseWrapper extends HttpServletResponseWrapper {

	private final ByteArrayOutputStream baos;

	private SgOutputStream sos;

	public SgResponseWrapper(HttpServletResponse response) {
		super(response);
		this.baos = new ByteArrayOutputStream();
	}

	@Override
	public ServletOutputStream getOutputStream() throws IOException {
		if (this.sos == null) {
			this.sos = new SgOutputStream(baos);
		}
		return this.sos;
	}

	public String getBody() {
		return new String(baos.toByteArray(), StandardCharsets.UTF_8);
	}
}
