type Request = {
  url: string;
  method: 'get'|'post'|'put'|'delete';
  body?: unknown;
  params?: unknown;
  callBack?: void | unknown;
};

type Response<T> = {
  ok: boolean;
  data?: T;
  message?: string;
};

type Error = {
  message: string;
};

const instance = axios.create({
  headers: {
    'Content-Type': 'application/json'
  },
  baseURL: 'http://localhost',
  timeout: 10000,
});

export const api = async <T>(request: Request): Promise<Response<T>> => {
  const source = axios.CancelToken.source();
  setTimeout(() => {
    source.cancel();
  }, 10000);
  const response = instance({
    url: request.url,
    method: request.method,
    data: request.body,
    params: request.params,
    cancelToken: source.token,
  })
    .then(data => {
      return { ok: true, data: data.data };
    })
    .catch(error => {
      let message;
      if (error.message === undefined) {
        message = 'System Error';
      } else if (typeof error.message === 'string') {
        message = error.message;
      } else {
        const response: Error = error.response.data;
        if (error instanceof axios.Cancel) {
          message = 'response timeout';
        } else {
          message = response.message;
        }
      }

      return {
        ok: false,
        message: message,
      };
    });

  return await response;
};

//////////////////////////////////////////////////////////////////////////////////////
type ResponseData = {
};

async call() {
  const response = await api<ResponseData>({
    url: '/test',
    method: 'get',
  });
  if (response.ok && response.data != undefined) {
    if (typeof response.data === 'string') {
      response.data = undefined;
    } else {
    }
  }
  return response;
}