package com.example.demo.config;

import java.io.DataOutputStream;
import java.io.IOException;
import java.io.OutputStream;
import jakarta.servlet.ServletOutputStream;
import jakarta.servlet.WriteListener;

public class SgOutputStream extends ServletOutputStream {

	private final DataOutputStream dos;

	public SgOutputStream(OutputStream output) {
		this.dos = new DataOutputStream(output);
	}

	@Override
	public void write(int b) throws IOException {
		this.dos.write(b);
	}

	@Override
	public boolean isReady() {
		return true;
	}

	@Override
	public void setWriteListener(WriteListener listener) {
	}
}
